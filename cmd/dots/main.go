package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
)

type selection struct {
	Name       string   `json:"name"`
	Profile    string   `json:"profile"`
	Groups     []string `json:"groups"`
	Configs    []string `json:"configs"`
	Kernel     string   `json:"kernel"`
	Bootloader string   `json:"bootloader"`
	Extras     []string `json:"extras"`
	Firefox    bool     `json:"firefox_privacy"`
	Spotify    bool     `json:"spotify_custom"`
}
type config struct {
	Label string `json:"label"`
	Group string `json:"group"`
}
type catalog struct {
	Groups  []string          `json:"groups"`
	Configs map[string]config `json:"configs"`
	Extras  map[string]string `json:"extras"`
	Stock   selection         `json:"stock"`
	Ryzen   selection         `json:"ryzen"`
}
type row struct {
	id, label string
	checked   bool
}
type previewMsg struct {
	content string
	err     error
}
type model struct {
	repo                          string
	catalog                       catalog
	selection                     selection
	rows                          []row
	stage, cursor, height, scroll int
	preview, errorText, action    string
	done, loading                 bool
}

func contains(values []string, target string) bool {
	for _, value := range values {
		if value == target {
			return true
		}
	}
	return false
}
func (m model) Init() tea.Cmd { return nil }
func (m *model) prepare() {
	m.cursor, m.scroll = 0, 0
	m.rows = nil
	switch m.stage {
	case 0:
		m.rows = []row{{"stock", "Stock — binary kernel, portable build settings", m.selection.Profile == "stock"}, {"fiw-ryzen", "Fiw's Ryzen — current Zen 5 tuning, custom + binary fallback", m.selection.Profile == "fiw-ryzen"}}
		if m.selection.Profile == "fiw-ryzen" {
			m.cursor = 1
		}
	case 1:
		for _, id := range m.catalog.Groups {
			label := id
			if id == "tidewm" {
				label += " (optional)"
			}
			m.rows = append(m.rows, row{id, label, contains(m.selection.Groups, id)})
		}
	case 2:
		ids := make([]string, 0, len(m.catalog.Configs))
		for id := range m.catalog.Configs {
			if id != "autostart" {
				ids = append(ids, id)
			}
		}
		sort.Strings(ids)
		for _, id := range ids {
			c := m.catalog.Configs[id]
			if c.Group != "" && !contains(m.selection.Groups, c.Group) {
				continue
			}
			m.rows = append(m.rows, row{id, c.Label, contains(m.selection.Configs, id)})
		}
	case 3:
		m.rows = []row{
			{"binary", "Kernel: generic binary", m.selection.Kernel == "binary"},
			{"custom", "Kernel: custom + generic binary fallback", m.selection.Kernel == "custom"},
			{"keep", "Bootloader: keep existing", m.selection.Bootloader == "keep"},
			{"limine", "Bootloader: optional Limine", m.selection.Bootloader == "limine"},
			{"grub", "Bootloader: optional GRUB", m.selection.Bootloader == "grub"},
		}
		for _, id := range []string{"nvidia", "btrfs", "filelight"} {
			m.rows = append(m.rows, row{id, m.catalog.Extras[id], contains(m.selection.Extras, id)})
		}
		m.rows = append(m.rows, row{"autostart", "Optional app autostart", contains(m.selection.Configs, "autostart")}, row{"firefox", "Optional Firefox-Privacy setup", m.selection.Firefox}, row{"spotify", "Optional Spotify customization script (stock by default)", m.selection.Spotify})
	}
}
func (m *model) remember() {
	switch m.stage {
	case 1:
		m.selection.Groups = []string{}
		for _, r := range m.rows {
			if r.checked {
				m.selection.Groups = append(m.selection.Groups, r.id)
			}
		}
	case 2:
		autostart := contains(m.selection.Configs, "autostart")
		m.selection.Configs = []string{}
		for _, r := range m.rows {
			if r.checked {
				m.selection.Configs = append(m.selection.Configs, r.id)
			}
		}
		if autostart {
			m.selection.Configs = append(m.selection.Configs, "autostart")
		}
	case 3:
		m.selection.Extras = []string{}
		for _, r := range m.rows {
			if _, ok := m.catalog.Extras[r.id]; ok && r.checked {
				m.selection.Extras = append(m.selection.Extras, r.id)
			}
			if r.checked && (r.id == "binary" || r.id == "custom") {
				m.selection.Kernel = r.id
			}
			if r.checked && (r.id == "keep" || r.id == "limine" || r.id == "grub") {
				m.selection.Bootloader = r.id
			}
			if r.id == "firefox" {
				m.selection.Firefox = r.checked
			}
			if r.id == "spotify" {
				m.selection.Spotify = r.checked
			}
		}
		configNames := []string{}
		for _, id := range m.selection.Configs {
			if id != "autostart" {
				configNames = append(configNames, id)
			}
		}
		for _, r := range m.rows {
			if r.id == "autostart" && r.checked {
				configNames = append(configNames, "autostart")
			}
		}
		m.selection.Configs = configNames
	}
}
func (m model) makePreview() tea.Cmd {
	return func() tea.Msg {
		file, err := os.CreateTemp("", "fiw-dots-selection-*.json")
		if err != nil {
			return previewMsg{err: err}
		}
		defer os.Remove(file.Name())
		data, err := json.Marshal(m.selection)
		if err == nil {
			_, err = file.Write(data)
		}
		file.Close()
		if err != nil {
			return previewMsg{err: err}
		}
		cmd := exec.Command("python3", filepath.Join(m.repo, "lib", "rice.py"), "--plan", "--selection", file.Name())
		output, err := cmd.CombinedOutput()
		return previewMsg{string(output), err}
	}
}
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch v := msg.(type) {
	case tea.WindowSizeMsg:
		m.height = v.Height
	case previewMsg:
		m.loading = false
		m.preview = v.content
		if v.err != nil {
			m.errorText = v.err.Error()
		}
	case tea.KeyMsg:
		key := v.String()
		if key == "ctrl+c" || key == "q" {
			return m, tea.Quit
		}
		if m.loading {
			return m, nil
		}
		if m.stage == 4 {
			switch key {
			case "up", "k":
				if m.scroll > 0 {
					m.scroll--
				}
			case "down", "j":
				if m.scroll < len(strings.Split(m.preview, "\n"))-1 {
					m.scroll++
				}
			case "esc":
				m.stage--
				m.prepare()
			case "enter", "s", "a", "i":
				if m.errorText == "" {
					m.done = true
					m.action = key
					return m, tea.Quit
				}
			}
			return m, nil
		}
		switch key {
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(m.rows)-1 {
				m.cursor++
			}
		case " ":
			if len(m.rows) == 0 {
				break
			}
			if m.stage == 0 {
				if m.rows[m.cursor].id == "stock" {
					m.selection = m.catalog.Stock
				} else {
					m.selection = m.catalog.Ryzen
				}
				m.prepare()
			} else {
				id := m.rows[m.cursor].id
				if m.stage == 3 && (id == "binary" || id == "custom") {
					for i := range m.rows {
						if m.rows[i].id == "binary" || m.rows[i].id == "custom" {
							m.rows[i].checked = false
						}
					}
					m.rows[m.cursor].checked = true
				} else if m.stage == 3 && (id == "keep" || id == "limine" || id == "grub") {
					for i := range m.rows {
						if m.rows[i].id == "keep" || m.rows[i].id == "limine" || m.rows[i].id == "grub" {
							m.rows[i].checked = false
						}
					}
					m.rows[m.cursor].checked = true
				} else {
					m.rows[m.cursor].checked = !m.rows[m.cursor].checked
				}
			}
		case "enter":
			if m.stage == 0 {
				if m.rows[m.cursor].id == "stock" {
					m.selection = m.catalog.Stock
				} else {
					m.selection = m.catalog.Ryzen
				}
			}
			m.remember()
			m.stage++
			if m.stage == 4 {
				m.loading = true
				m.errorText = ""
				return m, m.makePreview()
			}
			m.prepare()
		case "esc":
			if m.stage > 0 {
				m.remember()
				m.stage--
				m.prepare()
			}
		}
	}
	return m, nil
}

func (m model) View() string {
	const purple = "\033[38;2;157;143;217m"
	const reset = "\033[0m"
	titles := []string{"Preset", "Package sections", "Optional app configs", "Kernel, bootloader and extras", "Final preview"}
	text := purple + "  Fiw-Gentoo-Dots\n" + reset + "  " + titles[m.stage] + "  ·  " + m.selection.Name + "\n\n"
	budget := m.height - 10
	if budget < 5 {
		budget = 5
	}
	if m.stage == 4 {
		if m.loading {
			return text + "  Preparing preview…\n"
		}
		lines := strings.Split(m.preview, "\n")
		end := m.scroll + budget
		if end > len(lines) {
			end = len(lines)
		}
		for _, line := range lines[m.scroll:end] {
			text += "  " + line + "\n"
		}
		text += "\n  ↑/↓ scroll · Esc back · Enter save plan · a restore configs · i install packages\n  q cancel\n"
		if m.errorText != "" {
			text += "  " + m.errorText + "\n"
		}
		return text
	}
	start := 0
	if m.cursor >= budget {
		start = m.cursor - budget + 1
	}
	end := start + budget
	if end > len(m.rows) {
		end = len(m.rows)
	}
	for i := start; i < end; i++ {
		r := m.rows[i]
		mark := "[ ]"
		if r.checked {
			mark = "[✓]"
		}
		cursor := "  "
		if m.cursor == i {
			cursor = "› "
		}
		line := "  " + cursor + mark + " " + r.label
		if m.cursor == i {
			line = purple + line + reset
		}
		text += line + "\n"
	}
	return text + "\n  ↑/↓ move · Space select · Enter next · Esc back · q cancel\n"
}

func main() {
	repo, err := os.Getwd()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	output, err := exec.Command("python3", filepath.Join(repo, "lib", "rice.py"), "--catalog").Output()
	if err != nil {
		fmt.Fprintln(os.Stderr, "Cannot load the installer catalogue:", err)
		os.Exit(1)
	}
	var c catalog
	if err := json.Unmarshal(output, &c); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	m := model{repo: repo, catalog: c, selection: c.Stock, height: 28}
	m.prepare()
	result, err := tea.NewProgram(m, tea.WithAltScreen()).Run()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	final := result.(model)
	if !final.done {
		return
	}
	path := filepath.Join(repo, "local", "selection.json")
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	data, _ := json.MarshalIndent(final.selection, "", "  ")
	if err := os.WriteFile(path, append(data, '\n'), 0600); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println(final.preview)
	fmt.Println("\nSaved selection:", path)
	args := []string{filepath.Join(repo, "lib", "rice.py"), "--selection", path}
	switch final.action {
	case "a":
		args = append(args, "--apply-configs")
	case "i":
		args = append([]string{"python3"}, args...)
		args = append(args, "--install-packages")
	default:
		fmt.Println("Review the setup notes in docs/setup.md before applying.")
		return
	}
	program := "python3"
	if final.action == "i" {
		program = "sudo"
	}
	cmd := exec.Command(program, args...)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
