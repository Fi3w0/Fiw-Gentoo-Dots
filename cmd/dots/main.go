package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/x/ansi"
)

var tuiVersion = "source"

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
	Flatpaks   []string `json:"flatpaks"`
	Services   []string `json:"services"`
}
type config struct {
	Label string `json:"label"`
	Group string `json:"group"`
}
type setupOption struct {
	Label string `json:"label"`
	Group string `json:"group"`
	Scope string `json:"scope"`
}

type catalog struct {
	Groups   []string               `json:"groups"`
	Configs  map[string]config      `json:"configs"`
	Extras   map[string]string      `json:"extras"`
	Flatpaks map[string]setupOption `json:"flatpaks"`
	Services map[string]setupOption `json:"services"`
	Stock    selection              `json:"stock"`
	Ryzen    selection              `json:"ryzen"`
}
type row struct {
	id, label string
	checked   bool
}
type previewMsg struct {
	content string
	err     error
}
type backupChoice struct {
	ID    string `json:"id"`
	Count int    `json:"count"`
}
type backupsMsg struct {
	choices []backupChoice
	err     error
}
type model struct {
	repo                                 string
	catalog                              catalog
	selection                            selection
	rows                                 []row
	stage, cursor, height, width, scroll int
	preview, errorText, action, backupID string
	done, loading                        bool
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
	case 4:
		flatpaks := make([]string, 0, len(m.catalog.Flatpaks))
		for id := range m.catalog.Flatpaks {
			flatpaks = append(flatpaks, id)
		}
		sort.Strings(flatpaks)
		for _, id := range flatpaks {
			option := m.catalog.Flatpaks[id]
			m.rows = append(m.rows, row{"flatpak:" + id, "Flatpak: " + option.Label + " (" + option.Group + ")", contains(m.selection.Flatpaks, id)})
		}
		for _, id := range []string{"audio", "network", "bluetooth", "power"} {
			if option, ok := m.catalog.Services[id]; ok {
				m.rows = append(m.rows, row{"service:" + id, option.Label, contains(m.selection.Services, id)})
			}
		}
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
	case 4:
		m.selection.Flatpaks, m.selection.Services = []string{}, []string{}
		for _, r := range m.rows {
			if !r.checked {
				continue
			}
			if strings.HasPrefix(r.id, "flatpak:") {
				m.selection.Flatpaks = append(m.selection.Flatpaks, strings.TrimPrefix(r.id, "flatpak:"))
			}
			if strings.HasPrefix(r.id, "service:") {
				m.selection.Services = append(m.selection.Services, strings.TrimPrefix(r.id, "service:"))
			}
		}
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
func (m model) loadBackups() tea.Cmd {
	return func() tea.Msg {
		output, err := exec.Command("python3", filepath.Join(m.repo, "lib", "rice.py"), "--list-backups").CombinedOutput()
		var choices []backupChoice
		if err == nil {
			err = json.Unmarshal(output, &choices)
		} else {
			err = fmt.Errorf("%s", strings.TrimSpace(string(output)))
		}
		return backupsMsg{choices, err}
	}
}
func (m model) backupPreview() tea.Cmd {
	return func() tea.Msg {
		output, err := exec.Command("python3", filepath.Join(m.repo, "lib", "rice.py"), "--backup-plan", m.backupID).CombinedOutput()
		return previewMsg{string(output), err}
	}
}
func (m model) previewLines() []string {
	width := m.width
	if width == 0 {
		width = 80
	}
	if width < 10 {
		width = 10
	}
	return strings.Split(ansi.Wrap(m.preview, width-4, ""), "\n")
}
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch v := msg.(type) {
	case tea.WindowSizeMsg:
		m.height = v.Height
		m.width = v.Width
		if m.scroll >= len(m.previewLines()) {
			m.scroll = len(m.previewLines()) - 1
		}
	case previewMsg:
		m.loading = false
		m.preview = v.content
		if v.err != nil {
			m.errorText = v.err.Error()
		}
	case backupsMsg:
		m.loading = false
		m.rows = nil
		if v.err != nil {
			m.errorText = v.err.Error()
		}
		for _, choice := range v.choices {
			m.rows = append(m.rows, row{choice.ID, fmt.Sprintf("%s — %d files", choice.ID, choice.Count), false})
		}
	case tea.KeyMsg:
		key := v.String()
		if key == "ctrl+c" || key == "q" {
			return m, tea.Quit
		}
		if m.loading {
			return m, nil
		}
		if m.stage == 5 || m.stage == 7 {
			switch key {
			case "up", "k":
				if m.scroll > 0 {
					m.scroll--
				}
			case "down", "j":
				if m.scroll < len(m.previewLines())-1 {
					m.scroll++
				}
			case "esc":
				m.stage--
				m.prepare()
				if m.stage == 6 {
					m.loading = true
					m.errorText = ""
					return m, m.loadBackups()
				}
			case "u":
				if m.stage == 5 {
					m.stage = 6
					m.prepare()
					m.loading = true
					m.errorText = ""
					return m, m.loadBackups()
				}
			case "enter", "s", "a", "i", "f", "v", "b", "r":
				if m.errorText == "" {
					if m.stage == 7 {
						if key != "enter" {
							return m, nil
						}
						key = "u"
					}
					m.done = true
					m.action = key
					return m, tea.Quit
				}
			}
			return m, nil
		}
		if m.stage == 6 {
			switch key {
			case "up", "k":
				if m.cursor > 0 {
					m.cursor--
				}
			case "down", "j":
				if m.cursor < len(m.rows)-1 {
					m.cursor++
				}
			case "enter":
				if len(m.rows) > 0 && m.errorText == "" {
					m.backupID = m.rows[m.cursor].id
					m.stage = 7
					m.scroll = 0
					m.loading = true
					return m, m.backupPreview()
				}
			case "esc":
				m.stage = 5
				m.scroll = 0
				m.errorText = ""
				m.loading = true
				return m, m.makePreview()
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
			if m.stage == 5 {
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
	titles := []string{"Preset", "Package sections", "Optional app configs", "Kernel, bootloader and extras", "Flatpaks and optional services", "Final preview", "Config backups", "Restore backup preview"}
	text := purple + "  Fiw-Gentoo-Dots\n" + reset + "  " + titles[m.stage] + "  ·  " + m.selection.Name + "\n\n"
	budget := m.height - 10
	if budget < 5 {
		budget = 5
	}
	if m.stage == 5 || m.stage == 7 {
		if m.loading {
			return text + "  Preparing preview…\n"
		}
		lines := m.previewLines()
		end := m.scroll + budget
		if end > len(lines) {
			end = len(lines)
		}
		for _, line := range lines[m.scroll:end] {
			text += "  " + line + "\n"
		}
		if m.stage == 7 {
			text += "\n  ↑/↓ scroll · Esc back · Enter restore with confirmation · q cancel\n"
		} else {
			text += "\n  ↑/↓ scroll · Esc back · Enter save · r full restore · a configs · i packages\n  f Flatpaks · v services · b bootloader · u config backups · q cancel\n"
		}
		if m.errorText != "" {
			text += "  " + m.errorText + "\n"
		}
		return text
	}
	if m.stage == 6 && (m.loading || len(m.rows) == 0 || m.errorText != "") {
		message := "No config backups yet. Backups are created when existing configs are replaced."
		if m.loading {
			message = "Loading config backups…"
		}
		if m.errorText != "" {
			message = m.errorText
		}
		return text + "  " + message + "\n\n  Esc back · q cancel\n"
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
	if m.stage == 6 {
		return text + "\n  ↑/↓ move · Enter preview backup · Esc back · q cancel\n"
	}
	return text + "\n  ↑/↓ move · Space select · Enter next · Esc back · q cancel\n"
}

func main() {
	if len(os.Args) == 2 && os.Args[1] == "--version" {
		fmt.Println("Fiw-Gentoo-Dots TUI " + tuiVersion)
		return
	}
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
	savedPath := filepath.Join(repo, "local", "selection.json")
	if saved, readErr := os.ReadFile(savedPath); readErr == nil {
		var previous selection
		if json.Unmarshal(saved, &previous) == nil && (previous.Profile == "stock" || previous.Profile == "fiw-ryzen") {
			m.selection = previous
			m.stage = 1
		}
	}
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
	runID := fmt.Sprintf("%s-%d", time.Now().UTC().Format("20060102T150405.000000000Z"), os.Getpid())
	run := func(action string, root bool, extra ...string) error {
		args := []string{filepath.Join(repo, "lib", "rice.py"), "--selection", path, "--run-id", runID, action}
		args = append(args, extra...)
		program := "python3"
		if root {
			program = "sudo"
			args = append([]string{"python3"}, args...)
		}
		cmd := exec.Command(program, args...)
		cmd.Stdin, cmd.Stdout, cmd.Stderr = os.Stdin, os.Stdout, os.Stderr
		return cmd.Run()
	}
	services := func() error {
		system, user := false, false
		for _, id := range final.selection.Services {
			if c.Services[id].Scope == "system" {
				system = true
			}
			if c.Services[id].Scope == "user" {
				user = true
			}
		}
		if system {
			if err := run("--enable-services", true); err != nil {
				return err
			}
		}
		if user {
			return run("--enable-services", false)
		}
		if !system {
			fmt.Println("No services selected.")
		}
		return nil
	}
	var actionErr error
	workflow := "restore"
	switch final.action {
	case "a":
		workflow = "configs"
		actionErr = run("--apply-configs", false)
	case "i":
		workflow = "packages"
		actionErr = run("--install-packages", true)
	case "f":
		workflow = "flatpaks"
		actionErr = run("--install-flatpaks", false)
	case "v":
		workflow = "services"
		actionErr = services()
	case "b":
		workflow = "boot"
		actionErr = run("--deploy-bootloader", true)
	case "u":
		workflow = "backup"
		actionErr = run("--restore-backup", false, final.backupID)
	case "r":
		actionErr = run("--check-configs", false)
		if actionErr == nil && (len(final.selection.Groups) > 0 || len(final.selection.Extras) > 0 || final.selection.Bootloader != "keep" || len(final.selection.Flatpaks) > 0 || len(final.selection.Services) > 0) {
			actionErr = run("--install-packages", true)
		}
		if actionErr == nil && len(final.selection.Flatpaks) > 0 {
			actionErr = run("--install-flatpaks", false)
		}
		if actionErr == nil && len(final.selection.Services) > 0 {
			actionErr = services()
		}
		if actionErr == nil && len(final.selection.Configs) > 0 {
			actionErr = run("--apply-configs", false)
		}
		if actionErr == nil && final.selection.Bootloader != "keep" {
			actionErr = run("--deploy-bootloader", true)
		}
	default:
		fmt.Println("Saved. Choose an action in the TUI or use the commands in docs/setup.md.")
		return
	}
	summaryArgs := []string{"--workflow", workflow}
	if actionErr != nil {
		summaryArgs = append(summaryArgs, "--execution-error", actionErr.Error())
	}
	if summaryErr := run("--summary", false, summaryArgs...); summaryErr != nil {
		fmt.Fprintln(os.Stderr, "Cannot create the combined report:", summaryErr)
	}
	if actionErr != nil {
		var exitError *exec.ExitError
		if errors.As(actionErr, &exitError) && exitError.ExitCode() == 130 {
			fmt.Println("Cancelled. Completed steps remain recorded in the summary.")
			os.Exit(130)
		}
		fmt.Fprintln(os.Stderr, actionErr)
		os.Exit(1)
	}
}
