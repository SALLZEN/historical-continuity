#!/usr/bin/env Rscript
# E.03 stepwise field-display export: original readable plot construction.
# No model refitting, Quartz device, personal destination, or research-tree sync.
args <- commandArgs(trailingOnly=TRUE)
root <- normalizePath(if(length(args)) args[[1]] else getwd(), mustWork=TRUE)
stopifnot(file.exists(file.path(root,"config/workspace.json")))
suppressPackageStartupMessages({library(arrow);library(dplyr);library(forcats);library(ggplot2);library(ggsci);library(grid);library(patchwork);library(rcartocolor);library(scales);library(stringr)})
dir.create(file.path(root,".runtime/fontconfig/cache"),recursive=TRUE,showWarnings=FALSE)
font_dir <- file.path(root,"resources/fonts")
conf_dir <- file.path(root,".runtime/fontconfig")
xml_path <- function(p) gsub("&","&amp;",p,fixed=TRUE)
writeLines(paste0("<?xml version=\"1.0\"?><!DOCTYPE fontconfig SYSTEM \"fonts.dtd\"><fontconfig><dir>",xml_path(font_dir),"</dir><cachedir>",xml_path(file.path(conf_dir,"cache")),"</cachedir><alias><family>DAMADI STIX Two Text</family><prefer><family>STIX Two Text</family></prefer></alias></fontconfig>"),file.path(conf_dir,"fonts.conf"))
Sys.setenv(FONTCONFIG_FILE=file.path(conf_dir,"fonts.conf"),FONTCONFIG_PATH=conf_dir,PANGOCAIRO_BACKEND="fc")
source(file.path(root,"scripts/modules/pdf-export.R"))
register_damadi_fonts(font_dir)
update_geom_defaults("text",list(family="DAMADI STIX Two Text"))
svglite::svglite(file.path(root,".runtime/r-metrics-device.svg"),width=156/25.4,height=(156 * 5.68 / 7.25)/25.4,pointsize=9,bg="white")
metrics_device <- dev.cur()
# 1. Load the frozen inputs; the shared Python driver validates their SHA-256 hashes.
papers_data <- read_parquet(file.path(root,"inputs/papers.parquet"),col_select=c("bibcode","year","doctype"))
paper_arxiv_classes <- read_parquet(file.path(root,"inputs/paper_arxiv_classes.parquet"))
paper_citations <- read_parquet(file.path(root,"inputs/paper_citations.parquet"))
# 2. Resolve primary classes and construct the original field/subclass displays.

# primary_arxiv_class
primary_arxiv_class <- select(distinct(arrange(paper_arxiv_classes, bibcode, class_pos), bibcode, .keep_all = TRUE), 
    bibcode, arxiv_class, arxiv_category)

# paper_metadata
paper_metadata <- left_join(select(papers_data, bibcode, year, doctype), primary_arxiv_class, by = "bibcode")

# bh_id
bh_id <- "2018RvMP...90d5002B"

# bh_citers
bh_citers <- distinct(filter(paper_citations, bibcode == bh_id), citing_bibcode)

# bh_citers_meta
bh_citers_meta <- left_join(bh_citers, paper_metadata, by = c(citing_bibcode = "bibcode"))

# arxiv_plot_data
arxiv_plot_data <- ungroup(mutate(group_by(count(filter(filter(bh_citers_meta, !is.na(arxiv_category)), !arxiv_category %in% 
    c("nuclear physics", "quantum physics")), arxiv_category, arxiv_class, name = "n"), arxiv_category), total_n = sum(n)))

# category_order
category_order <- pull(arrange(distinct(arxiv_plot_data, arxiv_category, total_n), desc(total_n), arxiv_category), 
    arxiv_category)

# arxiv_plot_data
arxiv_plot_data <- ungroup(mutate(arxiv_plot_data, arxiv_category = factor(as.character(arxiv_category), levels = category_order), 
    category_label = factor(as.character(arxiv_category), levels = category_order), subclass_share = n/total_n))

# category_palette_names
category_palette_names <- c(astrophysics = "pink", `high-energy physics` = "cyan", `general relativity and quantum cosmology` = "indigo", 
    physics = "amber")

# build_family_palette
build_family_palette <- function(data, palette_name) {
    ordered_classes <- pull(arrange(data, n, arxiv_class), arxiv_class)
    n_classes <- length(ordered_classes)
    full_gradient <- (ggsci::pal_material(palette = palette_name))(10)
    if (n_classes == 1) {
        family_colors <- full_gradient[7]
    }
    else {
        family_colors <- (grDevices::colorRampPalette(full_gradient[2:10]))(n_classes)
    }
    stats::setNames(family_colors, ordered_classes)
}

# hex_luminance
hex_luminance <- function(colors) {
    rgb_matrix <- grDevices::col2rgb(colors)
    as.numeric(c(0.2126, 0.7152, 0.0722) %*% rgb_matrix)
}

# class_palette_list
class_palette_list <- lapply(split(arxiv_plot_data, factor(arxiv_plot_data$arxiv_category, levels = category_order)), 
    function(category_data) {
        palette_name <- category_palette_names[[as.character(category_data$arxiv_category[[1]])]]
        build_family_palette(category_data, palette_name)
    })

# class_palette
class_palette <- do.call(c, unname(class_palette_list))

# category_palette
category_palette <- stats::setNames(vapply(class_palette_list, function(palette_vec) unname(palette_vec[[length(palette_vec)]]), 
    character(1)), names(class_palette_list))

# category_levels
category_levels <- rev(category_order)

# category_totals
category_totals <- mutate(distinct(arxiv_plot_data, arxiv_category, total_n), category_label = as.character(arxiv_category), 
    arxiv_category = factor(as.character(arxiv_category), levels = category_levels), category_label = factor(category_label, 
        levels = category_levels))

# max_legend_columns
max_legend_columns <- max(lengths(class_palette_list))

# legend_plot_data
legend_plot_data <- do.call(rbind, lapply(seq_along(rev(class_palette_list)), function(i) {
    category_classes <- rev(class_palette_list)[[i]]
    ordered_class_names <- rev(names(category_classes))
    ordered_fill_colors <- rev(unname(category_classes))
    class_positions <- seq_along(ordered_class_names)
    data.frame(row_id = i, class_name = ordered_class_names, fill_color = ordered_fill_colors, class_position = class_positions, 
        stringsAsFactors = FALSE)
}))

# class_order
class_order <- pull(arrange(mutate(arxiv_plot_data, arxiv_category = factor(arxiv_category, levels = category_order), 
    class_color = unname(class_palette[as.character(arxiv_class)]), class_luminance = hex_luminance(class_color)), 
    desc(total_n), arxiv_category, desc(n), class_luminance, arxiv_class), arxiv_class)

# class_label_data
class_label_data <- select(arrange(mutate(arxiv_plot_data, arxiv_category = factor(arxiv_category, levels = category_order), 
    arxiv_class = factor(arxiv_class, levels = class_order), legend_label = paste0(as.character(arxiv_class), " (n = ", 
        scales::comma(n), ")")), arxiv_class), arxiv_class, legend_label)

# class_label_map
class_label_map <- stats::setNames(class_label_data$legend_label, as.character(class_label_data$arxiv_class))

# arxiv_plot_data
arxiv_plot_data <- arrange(mutate(arxiv_plot_data, arxiv_category = factor(arxiv_category, levels = category_levels), 
    category_label = factor(as.character(category_label), levels = category_levels), arxiv_class = factor(arxiv_class, 
        levels = class_order)), desc(total_n), arxiv_category, desc(n), arxiv_class)

# allocate_squares
allocate_squares <- function(shares, total_squares = 100) {
    raw_squares <- shares/sum(shares) * total_squares
    base_squares <- floor(raw_squares)
    remainder <- total_squares - sum(base_squares)
    if (remainder > 0) {
        promote_idx <- order(raw_squares - base_squares, decreasing = TRUE)[seq_len(remainder)]
        base_squares[promote_idx] <- base_squares[promote_idx] + 1L
    }
    if (remainder < 0) {
        demote_idx <- order(raw_squares - base_squares, decreasing = FALSE)[seq_len(abs(remainder))]
        base_squares[demote_idx] <- pmax(0L, base_squares[demote_idx] - 1L)
    }
    as.integer(base_squares)
}

# choose_total_squares
choose_total_squares <- function(weights, max_total_squares = Inf) {
    total_weight <- as.integer(round(sum(weights)))
    if (is.infinite(max_total_squares)) {
        return(total_weight)
    }
    min(total_weight, as.integer(max_total_squares))
}

# make_waffle_tiles
make_waffle_tiles <- function(data, n_cols = 20, normalized = FALSE, squares_per_category = 100) {
    base_data <- ungroup(mutate(group_by(arrange(mutate(data, arxiv_category = factor(as.character(arxiv_category), 
        levels = category_order), category_label = factor(as.character(category_label), levels = category_order), 
        class_color = unname(class_palette[as.character(arxiv_class)]), class_luminance = hex_luminance(class_color)), 
        desc(total_n), arxiv_category, desc(n), class_luminance, arxiv_class), arxiv_category, category_label, 
        total_n), tile_n = if (normalized) {
        allocate_squares(subclass_share, total_squares = squares_per_category)
    }
    else {
        n
    }))
    label_data <- mutate(arrange(distinct(base_data, arxiv_category, category_label, total_n), desc(total_n), arxiv_category), 
        category_label_wrapped = stringr::str_wrap(as.character(category_label), width = 20), panel_label = if (normalized) {
            paste0(category_label_wrapped, "\n(100-square composition)")
        }
        else {
            paste0(category_label_wrapped, "\n(n = ", scales::comma(total_n), ")")
        })
    ungroup(mutate(group_by(select(mutate(left_join(tidyr::uncount(base_data, tile_n), label_data, by = c("arxiv_category", 
        "category_label", "total_n")), panel_label = factor(panel_label, levels = label_data$panel_label)), -class_color, 
        -class_luminance), arxiv_category), tile_id = row_number(), x = ((tile_id - 1L)%%n_cols) + 1L, y = ceiling(tile_id/n_cols)))
}

# make_total_normalized_waffle_tiles
make_total_normalized_waffle_tiles <- function(data, n_cols = 25, total_squares = NULL, max_total_squares = Inf) {
    if (is.null(total_squares)) {
        total_squares <- choose_total_squares(data$n, max_total_squares = max_total_squares)
    }
    base_data <- select(arrange(mutate(data, arxiv_category = factor(as.character(arxiv_category), levels = category_order), 
        category_label = factor(as.character(category_label), levels = category_order), class_color = unname(class_palette[as.character(arxiv_class)]), 
        class_luminance = hex_luminance(class_color), tile_n = allocate_squares(n, total_squares = total_squares)), 
        desc(total_n), arxiv_category, desc(n), class_luminance, arxiv_class), -class_color, -class_luminance)
    mutate(tidyr::uncount(base_data, tile_n), tile_id = row_number(), x = ((tile_id - 1L)%%n_cols) + 1L, y = ceiling(tile_id/n_cols))
}

# waffle_fill_scale
waffle_fill_scale <- function() {
    scale_fill_manual(values = class_palette, breaks = class_order, labels = class_label_map[class_order], drop = FALSE)
}

# waffle_legend_guide
waffle_legend_guide <- function(ncol = 1) {
    guide_legend(ncol = ncol, byrow = TRUE, title.position = "top", keyheight = grid::unit(0.88, "lines"), keywidth = grid::unit(0.75, 
        "lines"), override.aes = list(color = NA))
}

# waffle_plot_theme
waffle_plot_theme <- function(base_family = "DAMADI STIX Two Text", base_size = 9, show_legend = TRUE) {
    theme_minimal(base_size = base_size) + theme(panel.grid = element_blank(), axis.title = element_blank(), axis.text = element_blank(), 
        axis.ticks = element_blank(), legend.position = if (show_legend) 
            "right"
        else "none", legend.title = element_blank(), legend.text = element_text(size = rel(1), lineheight = 0.96), 
        legend.box = "vertical", legend.justification = "left", legend.margin = margin(t = 3, l = 0), legend.spacing.x = grid::unit(0.1, 
            "lines"), legend.spacing.y = grid::unit(0.1, "lines"), plot.title.position = "plot", plot.caption.position = "plot")
}

# plot_arxiv_waffle
plot_arxiv_waffle <- function(tile_data, title = NULL, subtitle = NULL, caption = NULL, ncol = 4) {
    tile_data <- mutate(tile_data, panel_label = forcats::fct_rev(panel_label))
    ggplot(tile_data, aes(x = x, y = y, fill = arxiv_class)) + geom_tile(color = "white", linewidth = 0.05, width = 0.96, 
        height = 0.96, alpha = 0.85) + coord_equal() + facet_wrap(~panel_label, ncol = ncol, scales = "fixed", 
        labeller = label_value) + waffle_fill_scale() + scale_x_continuous(expand = expansion(mult = c(0.01, 0.01))) + 
        scale_y_continuous(expand = expansion(mult = c(0.01, 0.01))) + labs(title = title, subtitle = subtitle, 
        caption = caption, fill = "arXiv class", x = NULL, y = NULL) + waffle_plot_theme(show_legend = FALSE) + theme(text = element_text(family = "DAMADI STIX Two Text"), 
        strip.text = element_text(size = 9.5, lineheight = 1, margin = margin(t = 0, r = 12, b = 2, l = 12)), panel.spacing.x = grid::unit(0.5, 
            "cm"), panel.spacing.y = grid::unit(0.5, "cm"))
}

# plot_arxiv_single_waffle
plot_arxiv_single_waffle <- function(tile_data, title = NULL, subtitle = NULL, caption = NULL) {
    ggplot(tile_data, aes(x = x, y = y, fill = arxiv_class)) + geom_tile(color = "white", linewidth = 0.15, width = 0.96, 
        height = 0.96, alpha = 0.85) + coord_equal() + waffle_fill_scale() + scale_x_continuous(expand = expansion(mult = c(0.01, 
        0.01))) + scale_y_continuous(expand = expansion(mult = c(0.01, 0.01))) + labs(title = title, subtitle = subtitle, 
        caption = caption, fill = "arXiv class") + waffle_plot_theme(show_legend = TRUE) + guides(fill = waffle_legend_guide(ncol = 1)) + 
        theme(legend.key.height = grid::unit(0.72, "lines"), legend.key.width = grid::unit(0.6, "lines"))
}

# two_panel_left
two_panel_left <- ggplot(category_totals, aes(x = total_n, y = category_label, fill = arxiv_category)) + coord_flip() + 
    geom_col(width = 0.55, alpha = 0.75) + geom_text(aes(label = total_n), hjust = 0.5, vjust = 2, size = 3.9, 
    color = "white") + scale_y_discrete(labels = NULL) + scale_x_continuous(labels = comma, breaks = c(0, 50, 100, 
    150, 200, 250), expand = expansion(mult = c(0, 0.1))) + scale_fill_manual(values = category_palette) + labs(x = "Citations", 
    y = NULL, title = "Category totals") + theme_minimal(base_family = "DAMADI STIX Two Text") + theme(axis.title = element_text(size = 10), 
    axis.ticks.y = element_blank(), legend.position = "none", panel.grid.minor.x = element_blank(), panel.grid.minor.y = element_blank(), 
    panel.grid.major.x = element_blank(), plot.title = element_text(size = 10, face = "bold"))
two_panel_left <- two_panel_left + theme(axis.text=element_text(size=9),axis.title=element_text(size=10),plot.margin=margin(t=1,r=5.5,b=1,l=5.5))

# two_panel_right
two_panel_right <- ggplot(arxiv_plot_data, aes(x = subclass_share, y = category_label, fill = arxiv_class)) + geom_col(width = 0.55, 
    color = "white", linewidth = 0.25, alpha = 0.75) + scale_x_continuous(labels = percent_format(accuracy = 1), 
    expand = expansion(mult = c(0, 0.01))) + geom_text(data = distinct(arxiv_plot_data, category_label), aes(x = 0.015, 
    y = as.numeric(category_label) + 0.45, label = category_label), inherit.aes = FALSE, hjust = 0, vjust = 0.2, size = 3.5, family = "DAMADI STIX Two Text", 
    colour = "black") + scale_y_discrete(labels = scales::label_wrap(25), expand = expansion(add = c(0.4, 0.8))) + 
    scale_fill_manual(values = class_palette) + labs(x = NULL, y = NULL, title = "Subclass composition", fill = NULL) + 
    theme_minimal(base_family = "DAMADI STIX Two Text") + theme(axis.text.y = element_blank(), axis.ticks.y = element_blank(), 
    axis.title = element_text(size = 10), panel.grid.minor.x = element_blank(), plot.title = element_text(size = 10, 
        face = "bold"), legend.position = "none")
two_panel_right <- two_panel_right + theme(axis.text=element_text(size=9),axis.title=element_text(size=10),plot.margin=margin(t=1,r=5.5,b=1,l=5.5))

# custom_legend_plot
custom_legend_plot <- ggplot() + geom_tile(data = legend_plot_data, aes(x = class_position, y = -row_id, fill = fill_color), 
    width = 0.18, height = 0.55, show.legend = FALSE) + geom_text(data = legend_plot_data, aes(x = class_position + 
    0.12, y = -row_id, label = class_name), hjust = 0, size = 3.2) + scale_fill_identity() + scale_x_continuous(limits = c(0.7, 
    max_legend_columns + 1.15), expand = c(0, 0)) + scale_y_continuous(limits = c(-length(class_palette_list) - 
    0.5, 0), expand = c(0, 0)) + coord_cartesian(clip = "off") + theme_void() + theme(plot.margin = grid::unit(c(0, 
    0, 0, 0), "pt"))

# two_panel_main
two_panel_main <- two_panel_left + two_panel_right + plot_layout(axes = "collect_y", widths = c(1, 1.5))

# arxiv_plot
arxiv_plot <- two_panel_main/custom_legend_plot + plot_layout(heights = c(1, 0.34))

# absolute_tiles
absolute_tiles <- make_waffle_tiles(arxiv_plot_data, n_cols = 13, normalized = FALSE)

# absolute_waffle_plot
absolute_waffle_plot <- plot_arxiv_waffle(absolute_tiles, title = NULL, subtitle = NULL, caption = NULL)

# normalized_tiles
normalized_tiles <- make_total_normalized_waffle_tiles(arxiv_plot_data, n_cols = 25, max_total_squares = 500)

# normalized_waffle_plot
normalized_waffle_plot <- plot_arxiv_single_waffle(normalized_tiles, title = "arXiv class resolution", subtitle = NULL, 
    caption = NULL)

# waffle_design
waffle_design <- "\nAAAAA\nBBCCC\n"

# arxiv_waffle_plot
arxiv_waffle_plot <- absolute_waffle_plot/two_panel_left + two_panel_right + plot_layout(design = waffle_design, 
    heights = c(1, 1), guides = "keep") + plot_annotation(title = "Citing patterns across arXiv classes", 
    subtitle = "Absolute counts and within-category shares of BH citers by arXiv category and subclass.") & theme(plot.title = element_text(size = 11, 
    face = "bold", family = "DAMADI STIX Two Text"), plot.subtitle = element_text(size = 9, family = "DAMADI STIX Two Text"))

# 3. Check field counts against the accepted revision, then export at final size.
expected <- c("high-energy physics"=233L,"astrophysics"=180L,"general relativity and quantum cosmology"=76L,"physics"=48L)
actual <- setNames(category_totals$total_n,as.character(category_totals$arxiv_category))
stopifnot(identical(as.integer(actual[names(expected)]),unname(expected)))
stopifnot(nrow(absolute_tiles)==537L,nrow(normalized_tiles)==500L)
arxiv_waffle_plot <- arxiv_waffle_plot & theme(text=element_text(family="DAMADI STIX Two Text",size=9),strip.text=element_text(size=9.5,vjust=0,margin=margin(t=0,r=1,b=4,l=1)),plot.title=element_text(size=11,face="bold"),plot.subtitle=element_text(size=9))
save_damadi_pdf(arxiv_waffle_plot,file.path(root,"reproduced/figures/fig-arxiv-citing-patterns.pdf"),width_mm=156,height_mm=(156 * 5.68 / 7.25))
write.csv(arxiv_plot_data,file.path(root,"reproduced/analysis/waffle-subclass-counts.csv"),row.names=FALSE)
write.csv(data.frame(arxiv_category=names(category_palette),color=unname(category_palette)),file.path(root,"reproduced/analysis/figure-category-palette.csv"),row.names=FALSE)
writeLines(capture.output(sessionInfo()),file.path(root,"verification/r-session-info.txt"))
writeLines(c("displayed_records: 537","classified_records: 551","outside_display: 14","font: bundled STIX Two Text; Medium emphasis","profile_mm: 156 x 122.2179310345 (author aspect 7.25:5.68)"),file.path(root,"verification/waffle-checks.txt"))
dev.off(metrics_device)
cat("STIX waffle PDF exported; four-field counts and tile totals verified.\n")
