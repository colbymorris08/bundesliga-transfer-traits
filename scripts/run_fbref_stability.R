#!/usr/bin/env Rscript
# FBref Big-5 stability: prior league → first Bundesliga season
suppressPackageStartupMessages({
  library(worldfootballR)
  library(dplyr)
  library(tidyr)
  library(readr)
  library(stringr)
  library(jsonlite)
  library(tibble)
})

ROOT <- "/Users/colbymorris/bundesliga-transfer-traits"
OUT <- file.path(ROOT, "results")
CACHE <- file.path(OUT, "fbref_cache")
dir.create(CACHE, showWarnings = FALSE, recursive = TRUE)

SEASONS <- 2018:2025
STAT_TYPES <- c("standard", "shooting", "passing", "possession", "defense", "misc")
MIN_PRIOR <- 450
MIN_Y1 <- 450
STABILITY_GATE <- 0.50  # Step 2 primary gate
REF_GATE_040 <- 0.40
REDUNDANCY_GATE <- 0.70
MIN_PAIRS <- 25

numify <- function(x) {
  if (is.numeric(x)) return(as.numeric(x))
  as.numeric(gsub(",", "", as.character(x)))
}

load_one <- function(season, stat) {
  path <- file.path(CACHE, sprintf("%s_%d.csv", stat, season))
  if (file.exists(path)) return(read_csv(path, show_col_types = FALSE))
  message("Downloading ", stat, " ", season)
  df <- tryCatch(
    load_fb_big5_advanced_season_stats(
      season_end_year = season, stat_type = stat, team_or_player = "player"
    ),
    error = function(e) { message("  FAIL: ", conditionMessage(e)); NULL }
  )
  if (is.null(df) || nrow(df) == 0) return(NULL)
  write_csv(df, path)
  df
}

pieces <- list()
for (st in STAT_TYPES) {
  for (yr in SEASONS) {
    df <- load_one(yr, st)
    if (!is.null(df)) {
      df$.stat_type <- st
      pieces[[length(pieces) + 1]] <- df
    }
  }
}
message("pieces=", length(pieces))

# Keys + minutes from any table
get_minutes <- function(df) {
  nms <- names(df)
  if ("Min_Playing" %in% nms) return(numify(df$Min_Playing))
  if ("Min" %in% nms) return(numify(df$Min))
  if ("Mins_Per_90" %in% nms) return(numify(df$Mins_Per_90) * 90)
  if ("Mins_Per_90_Playing" %in% nms) return(numify(df$Mins_Per_90_Playing) * 90)
  rep(NA_real_, nrow(df))
}

to_keydf <- function(df) {
  tibble(
    season_end = df$Season_End_Year,
    player = as.character(df$Player),
    squad = as.character(df$Squad),
    comp = as.character(df$Comp),
    pos = as.character(df$Pos),
    url = if ("Url" %in% names(df)) as.character(df$Url) else NA_character_,
    minutes = get_minutes(df),
    .stat_type = df$.stat_type
  )
}

# Metric columns to keep per table (exclude meta)
META <- c("Season_End_Year","Squad","Comp","Player","Nation","Pos","Age","Born","Url",
          ".stat_type","Rk","Matches","Player_Href","MP_Playing","Starts_Playing",
          "Min_Playing","Mins_Per_90_Playing","Mins_Per_90","Min")

extract_metrics <- function(df) {
  nms <- setdiff(names(df), META)
  out <- to_keydf(df)
  for (col in nms) {
    v <- numify(df[[col]])
    if (all(is.na(v))) next
    # prefix with stat type if name collision risk — use raw names; resolve later
    safe <- make.names(col)
    # spaces in names like "Def 3rd_Tackles"
    safe <- gsub("\\.+", "_", safe)
    safe <- gsub("^_|_$", "", safe)
    # keep original-ish
    nm <- gsub(" ", "_", col)
    nm <- gsub("%", "_pct", nm)
    nm <- gsub("\\+", "_plus_", nm)
    nm <- gsub("/", "_per_", nm)
    nm <- gsub("-", "_minus_", nm)
    if (nm %in% names(out)) nm <- paste0(df$.stat_type[1], "__", nm)
    out[[nm]] <- v
  }
  out
}

all_tabs <- lapply(pieces, extract_metrics)
base <- bind_rows(Filter(function(d) identical(unique(d$.stat_type), "standard"), all_tabs))
message("standard rows=", nrow(base))

# Bind each non-standard stat type across seasons, then join once
keys <- c("season_end", "player", "squad", "comp")
wide <- base %>% select(-.stat_type)

for (st in setdiff(STAT_TYPES, "standard")) {
  tabs_st <- Filter(function(d) identical(unique(d$.stat_type), st), all_tabs)
  if (!length(tabs_st)) next
  add <- bind_rows(tabs_st) %>% select(-.stat_type, -minutes, -pos, -url)
  # collapse rare duplicate player-squad-comp-season rows
  add <- add %>%
    group_by(across(all_of(keys))) %>%
    summarise(across(everything(), ~ {
      v <- na.omit(.x)
      if (length(v)) v[[1]] else NA
    }), .groups = "drop")
  # new columns only (avoid .x/.y)
  new_cols <- setdiff(names(add), names(wide))
  overlap <- setdiff(intersect(names(add), names(wide)), keys)
  if (length(overlap)) {
    # coalesce into existing
    tmp <- wide %>% left_join(add %>% select(all_of(c(keys, overlap))), by = keys, suffix = c("", "__new"))
    for (col in overlap) {
      newc <- paste0(col, "__new")
      if (newc %in% names(tmp)) {
        tmp[[col]] <- dplyr::coalesce(tmp[[col]], tmp[[newc]])
        tmp[[newc]] <- NULL
      }
    }
    wide <- tmp
  }
  if (length(new_cols)) {
    wide <- wide %>% left_join(add %>% select(all_of(c(keys, new_cols))), by = keys)
  }
  message("joined ", st, " → cols=", ncol(wide),
          " eg nonNA ", new_cols[1], "=",
          if (length(new_cols)) sum(!is.na(wide[[new_cols[1]]])) else "n/a")
}
message("wide cols=", ncol(wide), " rows=", nrow(wide))

wide <- wide %>%
  mutate(
    player_id = if_else(!is.na(url) & url != "", url, paste0("name:", player)),
    is_bl = str_detect(comp, regex("Bundesliga", ignore_case = TRUE))
  ) %>%
  filter(is.finite(minutes), minutes > 0)

first_bl <- wide %>%
  filter(is_bl) %>%
  group_by(player_id) %>%
  summarise(first_bl_season = min(season_end), player_name = first(player), .groups = "drop")

y1 <- wide %>%
  filter(is_bl) %>%
  inner_join(first_bl, by = "player_id") %>%
  filter(season_end == first_bl_season, minutes >= MIN_Y1) %>%
  group_by(player_id) %>%
  slice_max(order_by = minutes, n = 1, with_ties = FALSE) %>%
  ungroup()

prior <- wide %>%
  filter(!is_bl) %>%
  inner_join(first_bl, by = "player_id") %>%
  filter(season_end < first_bl_season, minutes >= MIN_PRIOR) %>%
  group_by(player_id) %>%
  slice_max(order_by = season_end, n = 1, with_ties = FALSE) %>%
  group_by(player_id, season_end) %>%
  slice_max(order_by = minutes, n = 1, with_ties = FALSE) %>%
  ungroup()

pairs <- inner_join(y1, prior, by = "player_id", suffix = c("_y1", "_prior"))
message("pairs=", nrow(pairs), " y1=", nrow(y1))

# Metric bases present on both sides
meta_bases <- c("season_end","player","squad","comp","pos","url","minutes","player_id",
                "is_bl","first_bl_season","player_name")
y1_bases <- sub("_y1$", "", grep("_y1$", names(pairs), value = TRUE))
pr_bases <- sub("_prior$", "", grep("_prior$", names(pairs), value = TRUE))
metric_bases <- setdiff(intersect(y1_bases, pr_bases), meta_bases)

# Prefer rate/per90 columns; convert counts to per90
is_already_rate <- function(nm) {
  grepl("_Per$|_pct|per_90|Per90|_percent", nm, ignore.case = TRUE) ||
    grepl("Cmp_pct|Succ_pct|SoT_pct|Won_pct|Tkl_pct", nm)
}

make_val <- function(suffix, base) {
  v <- pairs[[paste0(base, "_", suffix)]]
  mins <- pairs[[paste0("minutes_", suffix)]]
  if (is_already_rate(base)) return(v)
  ifelse(is.finite(mins) & mins > 0, v / mins * 90, NA_real_)
}

# Drop near-duplicate families: prefer *_Per / rate over raw counts when both exist
prefer <- function(bases) {
  drop <- character()
  for (b in bases) {
    if (grepl("_Per$", b)) {
      raw <- sub("_Per$", "", b)
      # also Expected vs Per pairs handled in redundancy
      if (raw %in% bases) drop <- c(drop, raw)
    }
    if (grepl("_Expected$", b) && paste0(sub("_Expected$", "", b), "_Per") %in% bases) {
      # keep Per, drop Expected count
      drop <- c(drop, b)
    }
  }
  # prefer Sh_per_90_Standard over Sh_Standard etc.
  for (b in bases) {
    if (grepl("per_90", b, ignore.case = TRUE)) {
      raw <- gsub("_per_90", "", b, ignore.case = TRUE)
      raw2 <- gsub("per_90_", "", b, ignore.case = TRUE)
      if (raw %in% bases) drop <- c(drop, raw)
    }
  }
  setdiff(bases, unique(drop))
}

metric_bases <- prefer(metric_bases)
message("metrics after prefer=", length(metric_bases))

INVERT <- c("Mis_Performance", "Dis_Performance", "Err", "Fls", "Lost_Aerial", "Lost_Challenges",
            "Tkld_Take", "Mis_Carries", "Dis_Carries")

stab_list <- list()
for (base in metric_bases) {
  x <- make_val("prior", base)
  y <- make_val("y1", base)
  if (base %in% INVERT || grepl("^Mis_|^Dis_|^Err|Lost_|Tkld_", base)) {
    x <- -x; y <- -y
  }
  ok <- is.finite(x) & is.finite(y)
  n <- sum(ok)
  if (n < MIN_PAIRS) next
  if (sd(x[ok]) < 1e-8 || sd(y[ok]) < 1e-8) next
  r <- suppressWarnings(cor(x[ok], y[ok]))
  if (!is.finite(r)) next
  stab_list[[length(stab_list) + 1]] <- tibble(
    metric = base, n_pairs = n, stability_r = as.numeric(r),
    passes_0_40 = r >= REF_GATE_040,
    passes_0_50 = r >= STABILITY_GATE,
    passes_0_70 = r >= 0.70
  )
}

stab <- bind_rows(stab_list) %>% arrange(desc(stability_r))

categorize <- function(m) {
  if (grepl("Tkl|Int|Blocks|Clr|Err|Chall|Def|Aerial|Sh_Blocks|Pass_Blocks|Recov|Fls", m, ignore.case = TRUE)) return("Defending")
  if (grepl("Pass|PrgP|Cmp|Prog|Final|KP|xA|xAG|TB|Sw|Crs|CK|PrgDist_Total|TotDist_Total", m, ignore.case = TRUE)) return("Passing")
  if (grepl("Carr|PrgC|PrgR|Take|Drb|Mis|Dis|Touch|Att_Pen|CPA|Prog", m, ignore.case = TRUE)) return("Carrying")
  if (grepl("Gls|Ast|xG|npxG|Sh|SoT|SCA|GCA|Shot|PK", m, ignore.case = TRUE)) return("Attacking")
  "Other"
}
abbrevize <- function(m) {
  a <- gsub("_Expected|_Per|_Playing|_Progression|_Performance|_Standard|_Total|_Carries|_Touches|_Take|_Tackles|_Challenges|_Blocks|_Aerial|_Types", "", m)
  a <- gsub("_", "", a)
  toupper(substr(a, 1, min(5, nchar(a))))
}
nice_label <- function(m) {
  m <- gsub("_", " ", m)
  m <- gsub(" pct", "%", m)
  m <- gsub(" plus ", "+", m)
  m <- gsub(" per ", "/", m)
  m
}

stab <- stab %>% mutate(
  category = vapply(metric, categorize, character(1)),
  abbrev = vapply(metric, abbrevize, character(1)),
  label = vapply(metric, nice_label, character(1))
)

passed <- stab %>% filter(passes_0_50)
pass_metrics <- passed$metric

if (length(pass_metrics) >= 2) {
  y1_mat <- sapply(pass_metrics, function(b) make_val("y1", b))
  colnames(y1_mat) <- pass_metrics
  corm <- cor(y1_mat, use = "pairwise.complete.obs")
  red <- list()
  for (i in seq_along(pass_metrics)) {
    for (j in seq_len(i - 1)) {
      rr <- corm[i, j]
      if (is.finite(rr) && abs(rr) >= REDUNDANCY_GATE) {
        red[[length(red) + 1]] <- tibble(metric_a = pass_metrics[j], metric_b = pass_metrics[i], r = as.numeric(rr))
      }
    }
  }
  red_pairs <- bind_rows(red) %>% arrange(desc(abs(r)))
} else {
  red_pairs <- tibble(metric_a = character(), metric_b = character(), r = double())
  corm <- NULL
}

auto <- passed$metric
if (nrow(red_pairs) > 0) {
  drop <- character()
  for (k in seq_len(nrow(red_pairs))) {
    a <- red_pairs$metric_a[k]; b <- red_pairs$metric_b[k]
    if (a %in% drop || b %in% drop) next
    ra <- passed$stability_r[passed$metric == a][1]
    rb <- passed$stability_r[passed$metric == b][1]
    if (is.na(ra) || is.na(rb)) next
    if (ra >= rb) drop <- c(drop, b) else drop <- c(drop, a)
  }
  auto <- setdiff(auto, unique(drop))
}

# Outputs
write_csv(stab, file.path(OUT, "fbref_stability_all_metrics.csv"))
write_csv(stab %>% filter(passes_0_40), file.path(OUT, "fbref_stability_passed_r040.csv"))
write_csv(stab %>% filter(passes_0_50), file.path(OUT, "fbref_stability_passed_r050.csv"))
write_csv(stab %>% filter(passes_0_70), file.path(OUT, "fbref_stability_passed_r070.csv"))
write_csv(red_pairs, file.path(OUT, "fbref_redundancy_high_pairs_step2.csv"))
write_csv(tibble(metric = auto, note = "AUTO keep higher-stability side of each |r|>=0.70 pair; gate r>=0.50"),
          file.path(OUT, "fbref_redundancy_auto_shortlist_suggestion.csv"))

pairs_out <- tibble(
  player_id = pairs$player_id,
  player = pairs$player_y1,
  prior_season = pairs$season_end_prior,
  prior_comp = pairs$comp_prior,
  prior_squad = pairs$squad_prior,
  prior_minutes = pairs$minutes_prior,
  y1_season = pairs$season_end_y1,
  y1_squad = pairs$squad_y1,
  y1_minutes = pairs$minutes_y1,
  pos = pairs$pos_y1
)
write_csv(pairs_out, file.path(OUT, "fbref_inbound_pairs.csv"))

if (!is.null(corm)) {
  write_csv(as.data.frame(corm) %>% rownames_to_column("metric"),
            file.path(OUT, "fbref_redundancy_corr_passed_metrics.csv"))
}

summary <- list(
  source = "FBref Big 5 via worldfootballR load_fb_big5_advanced_season_stats",
  seasons_end_year = SEASONS,
  min_prior_minutes = MIN_PRIOR,
  min_y1_minutes = MIN_Y1,
  stability_gate = STABILITY_GATE,
  n_pairs = nrow(pairs),
  n_metrics_tested = nrow(stab),
  n_pass_0_40 = sum(stab$passes_0_40),
  n_pass_0_50 = sum(stab$passes_0_50),
  n_pass_0_70 = sum(stab$passes_0_70),
  n_redundancy_pairs = nrow(red_pairs),
  auto_shortlist_n = length(auto),
  auto_shortlist = auto
)
write_json(summary, file.path(OUT, "fbref_cohort_summary.json"), auto_unbox = TRUE, pretty = TRUE)

md <- c(
  "# FBref stability — Bundesliga inbound (Big 5)",
  "",
  sprintf("**Source:** %s", summary$source),
  sprintf("**Seasons (end years):** %s", paste(SEASONS, collapse = ", ")),
  sprintf("**Minutes:** prior ≥ %d · BL Y1 ≥ %d", MIN_PRIOR, MIN_Y1),
  sprintf("**Stability gate (Step 2):** **r ≥ %.2f**", STABILITY_GATE),
  sprintf("**Paired inbound N:** **%d**", nrow(pairs)),
  sprintf("**Metrics tested:** %d", nrow(stab)),
  sprintf("**Passed r ≥ 0.40:** %d", sum(stab$passes_0_40)),
  sprintf("**Passed r ≥ 0.50:** **%d**", sum(stab$passes_0_50)),
  sprintf("**Passed r ≥ 0.70:** **%d**", sum(stab$passes_0_70)),
  sprintf("**Redundancy pairs (among r≥0.50):** **%d**", nrow(red_pairs)),
  sprintf("**Auto shortlist:** **%d**", length(auto)),
  "",
  "## Metrics that passed r ≥ 0.50",
  "",
  "| Abbrev | Metric | Category | r | N |",
  "|---|---|---|---:|---:|"
)
pass_tbl <- stab %>% filter(passes_0_50)
for (i in seq_len(nrow(pass_tbl))) {
  md <- c(md, sprintf("| %s | %s | %s | %.3f | %d |",
                      pass_tbl$abbrev[i], pass_tbl$label[i], pass_tbl$category[i],
                      pass_tbl$stability_r[i], pass_tbl$n_pairs[i]))
}
md <- c(md, "", "## Redundancy pairs (|r|≥0.70 among r≥0.50)", "")
if (!nrow(red_pairs)) md <- c(md, "_None_") else {
  md <- c(md, "| A | B | r |", "|---|---|---:|")
  for (i in seq_len(min(40, nrow(red_pairs)))) {
    md <- c(md, sprintf("| %s | %s | %.3f |", red_pairs$metric_a[i], red_pairs$metric_b[i], red_pairs$r[i]))
  }
}
md <- c(md, "", "## Auto shortlist", "", paste0("- ", auto, collapse = "\n"))
writeLines(md, file.path(OUT, "FBREF_RESULTS.md"))

message("DONE n_pairs=", nrow(pairs), " tested=", nrow(stab),
        " pass050=", sum(stab$passes_0_50), " red=", nrow(red_pairs),
        " auto=", length(auto))
print(head(stab %>% filter(passes_0_50), 20))
