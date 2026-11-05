#!/usr/bin/env Rscript
# E.03: the author's ggplot specification, using verified revision values.
args <- commandArgs(trailingOnly = TRUE)
root <- normalizePath(if (length(args)) args[[1]] else getwd(), mustWork = TRUE)
stopifnot(file.exists(file.path(root, "config/workspace.json")))
suppressPackageStartupMessages({library(ggplot2);library(scales)})
if (!capabilities("aqua")) stop("The requested Quartz PDF export requires macOS R with Quartz support.")
source(file.path(root, "scripts/modules/quartz-fonts.R"))
register_damadi_quartz_fonts(
  file.path(root, "resources/fonts"),
  file.path(root, ".runtime/quartz-fonts"),
  file.path(root, "scripts/modules/register-quartz-fonts.c")
)
# Preserve the revised model predictions; only adapt column names for this plot.
verified <- read.csv(file.path(root, "reproduced/analysis/stratum-differences.csv"), check.names = FALSE)
stratum_plot_data <- verified
stratum_plot_data$diff_adj <- stratum_plot_data$difference
keep_categories <- c("astrophysics", "high-energy physics", "general relativity and quantum cosmology", "physics", "nuclear physics", "quantum physics")
stratum_plot_data$arxiv_category <- factor(stratum_plot_data$arxiv_category, levels = rev(keep_categories))
stratum_plot_data$year_bin <- factor(stratum_plot_data$year_bin, levels = c("2018–2019", "2020–2021", "2022–2023", "2024–2025"))
palette_data <- read.csv(file.path(root, "reproduced/analysis/figure-category-palette.csv"))
category_palette <- setNames(palette_data$color, palette_data$arxiv_category)
stopifnot(nrow(stratum_plot_data) == 12L, all(stratum_plot_data$n_bh >= 10), all(stratum_plot_data$n_nonbh >= 100))
stopifnot(identical(stratum_plot_data$diff_adj, verified$difference), all(as.character(stratum_plot_data$arxiv_category) %in% names(category_palette)))

stratum_plot <- ggplot(
  stratum_plot_data,
  aes(x = diff_adj, y = arxiv_category, size = n_bh, color = arxiv_category)
) +
  geom_vline(xintercept = 0, linetype = "dashed", linewidth = 0.3) +
  geom_point(alpha = 0.85) +
  facet_grid(~ year_bin) +
  scale_y_discrete(labels = scales::label_wrap(15)) +
  scale_x_continuous(
    labels = percent_format(accuracy = 1),
    breaks = seq(0.0, 0.10, by = 0.02)
  ) +
  coord_cartesian(xlim = c(0.0, 0.10)) +
  scale_color_manual(values = category_palette) +
  scale_size_continuous(range = c(5, 15), name = "# BH-citing papers") +
  guides(
    color = "none",
    size = guide_legend(
      title = "Review-citing papers:",
      position = "bottom",
      title.position = "left",
      nrow = 1
    )
  ) +
  theme_minimal(base_family = "STIX Two Text") +
  labs(
    x = "Adjusted probability difference (percentage points)",
    y = NULL,
    title = "Length-adjusted canon uptake among BH citers"
  ) +
  theme(
    panel.grid.minor.x = element_blank(),
    plot.title = element_text(size = 11, hjust = 0.5),
    axis.text.x = element_text(size = 8.5, hjust = 0.2),
    axis.text.y = element_text(size = 9, lineheight = 0.96),
    strip.text.x = element_text(size = 9.5, hjust = 0.5),
    strip.text.y = element_text(angle = 0),
    axis.title.x = element_text(size = 10),
    legend.title = element_text(size = 10),
    legend.text = element_text(size = 10),
    legend.margin = margin(t = 0, r = 0, b = 0, l = 0)
  )

# Outer page padding keeps the last 10% tick inside the PDF; supplied settings above are retained.
stratum_plot <- stratum_plot + theme(plot.margin = margin(t = 5.5, r = 9, b = 5.5, l = 5.5))

quartz(
  type = "pdf",
  file = file.path(root, "reproduced/figures/fig-cocitation-strata.pdf"),
  width = 7,
  height = 4,
  family = "STIX Two Text",
  bg = "white"
)
print(stratum_plot)
dev.off()
# Keep the actual display data, scale values, and session as inspectable records.
built <- ggplot_build(stratum_plot)
write.csv(stratum_plot_data, file.path(root, "reproduced/analysis/stratum-plot-data.csv"), row.names = FALSE)
drawn <- built$data[[2]]
stopifnot(nrow(drawn) == nrow(stratum_plot_data), all(is.finite(drawn$size)))
stopifnot(isTRUE(all.equal(drawn$x, stratum_plot_data$diff_adj)))
expected_sizes <- 5 + 10 * sqrt((stratum_plot_data$n_bh - min(stratum_plot_data$n_bh)) / diff(range(stratum_plot_data$n_bh)))
stopifnot(isTRUE(all.equal(drawn$size, expected_sizes)))
write.csv(data.frame(n_bh = stratum_plot_data$n_bh, diff_adj = stratum_plot_data$diff_adj, diameter_mm = drawn$size), file.path(root, "verification/stratum-size-scale.csv"), row.names = FALSE)
writeLines(capture.output(sessionInfo()), file.path(root, "verification/stratum-r-session-info.txt"))
writeLines(c("backend: Quartz PDF", "width_in: 7", "height_in: 4", "font: bundled STIX Two Text (process-local CoreText registration)", "plot: author-supplied ggplot specification, unchanged", "data: verified revision stratum predictions; no refit"), file.path(root, "verification/stratum-export.txt"))
cat("Author-specified ggplot exported with Quartz at 7 x 4 inches.\n")
