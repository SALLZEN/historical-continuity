# Portable SVG-to-PDF export; requires svglite, systemfonts, and rsvg-convert.
register_damadi_fonts <- function(font_dir) {
  # A private alias selects the bundled static TTFs even when macOS has another STIX release.
  systemfonts::register_font("DAMADI STIX Two Text",
    plain = file.path(font_dir, "STIXTwoText-Regular.ttf"),
    bold = file.path(font_dir, "STIXTwoText-Medium.ttf"),
    italic = file.path(font_dir, "STIXTwoText-Italic.ttf"),
    bolditalic = file.path(font_dir, "STIXTwoText-MediumItalic.ttf"))
}

save_damadi_pdf <- function(plot, destination, width_mm = 156, height_mm = 110) {
  stopifnot(tolower(tools::file_ext(destination)) == "pdf")
  converter <- Sys.which("rsvg-convert")
  if (!nzchar(converter)) stop("Install rsvg-convert before PDF export")
  dir.create(dirname(destination), recursive = TRUE, showWarnings = FALSE)
  render_dir <- file.path(dirname(destination), ".render-work")
  dir.create(render_dir, showWarnings = FALSE)
  svg <- tempfile(tmpdir = render_dir, fileext = ".svg")
  on.exit(unlink(svg), add = TRUE)
  svglite::svglite(svg, width = width_mm / 25.4, height = height_mm / 25.4,
    pointsize = 9, bg = "white")
  tryCatch(print(plot), finally = grDevices::dev.off())
  status <- system2(converter, c("--format=pdf", "--output", shQuote(destination), shQuote(svg)))
  if (status != 0L || !file.exists(destination) || file.info(destination)$size <= 0)
    stop("PDF export failed")
  invisible(destination)
}
