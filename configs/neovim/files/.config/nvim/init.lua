-- Colors
vim.opt.termguicolors = true
-- Load the bundled native theme package before applying the captured highlights.
pcall(vim.cmd.packadd, "catppuccin")
-- Keep a built-in fallback if the theme package is intentionally omitted.
if not pcall(vim.cmd.colorscheme, "catppuccin-mocha") then
  vim.o.background = "dark"
  vim.cmd.colorscheme "default"
end


-- Transparent background
vim.api.nvim_set_hl(0, "Normal",        { bg = "none", fg = "#E0D7FF" })
vim.api.nvim_set_hl(0, "NormalNC",      { bg = "none", fg = "#BFAAE0" })
vim.api.nvim_set_hl(0, "NormalFloat",   { bg = "none" })
vim.api.nvim_set_hl(0, "FloatBorder",   { fg = "#B388EB", bg = "none" })
vim.api.nvim_set_hl(0, "LineNr",        { fg = "#7A6FAF", bg = "none" })
vim.api.nvim_set_hl(0, "CursorLineNr",  { fg = "#CBA6F7", bold = true })
vim.api.nvim_set_hl(0, "Visual",        { bg = "#2A1E3D" })
vim.api.nvim_set_hl(0, "Comment",       { fg = "#7A6FAF", italic = true })
vim.api.nvim_set_hl(0, "String",        { fg = "#E0B0FF" })
vim.api.nvim_set_hl(0, "Keyword",       { fg = "#CBA6F7", bold = true })
vim.api.nvim_set_hl(0, "Function",      { fg = "#B388EB" })
vim.api.nvim_set_hl(0, "Type",          { fg = "#CBA6F7" })
vim.api.nvim_set_hl(0, "CursorLine",    { bg = "#2A1E3D" })
vim.api.nvim_set_hl(0, "StatusLine",    { fg = "#B388EB", bg = "none" })
vim.api.nvim_set_hl(0, "SignColumn",    { bg = "none" })
vim.api.nvim_set_hl(0, "EndOfBuffer",   { bg = "none", fg = "#1A1423" })
