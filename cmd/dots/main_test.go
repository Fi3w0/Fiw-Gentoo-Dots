package main

import (
	tea "github.com/charmbracelet/bubbletea"
	"strings"
	"testing"
)

func TestRyzenSelectionSurvivesSpaceAndEnter(t *testing.T) {
	c := catalog{Stock: selection{Name: "Stock", Profile: "stock"}, Ryzen: selection{Name: "Fiw's Ryzen", Profile: "fiw-ryzen"}}
	m := model{catalog: c, selection: c.Stock}
	m.prepare()
	m.cursor = 1
	next, _ := m.Update(tea.KeyMsg{Type: tea.KeySpace})
	m = next.(model)
	next, _ = m.Update(tea.KeyMsg{Type: tea.KeyEnter})
	m = next.(model)
	if m.selection.Profile != "fiw-ryzen" || m.stage != 1 {
		t.Fatalf("selected wrong preset: %+v", m.selection)
	}
}

func TestBootloaderChoicesAreExclusive(t *testing.T) {
	m := model{stage: 3, selection: selection{Kernel: "binary", Bootloader: "keep"}, catalog: catalog{Extras: map[string]string{}}}
	m.prepare()
	m.cursor = 4
	next, _ := m.Update(tea.KeyMsg{Type: tea.KeySpace})
	m = next.(model)
	m.remember()
	if m.selection.Bootloader != "grub" {
		t.Fatal("GRUB was not selected")
	}
	selected := 0
	for _, r := range m.rows {
		if r.checked && (r.id == "keep" || r.id == "limine" || r.id == "grub") {
			selected++
		}
	}
	if selected != 1 {
		t.Fatal("multiple bootloaders selected")
	}
}

func TestConfigsSelectableWithoutPackageGroups(t *testing.T) {
	m := model{stage: 2, catalog: catalog{Configs: map[string]config{
		"fish":  {Label: "Fish", Group: "cli"},
		"kitty": {Label: "Kitty", Group: "fiw-apps"},
	}}, selection: selection{Configs: []string{"fish"}}}
	m.prepare()
	if len(m.rows) != 2 || !m.rows[0].checked {
		t.Fatal("configs were hidden or deselected by package choices")
	}
}

func TestSetupCheckboxesSurviveFinalPreview(t *testing.T) {
	m := model{stage: 4, catalog: catalog{
		Flatpaks: map[string]setupOption{"org.vinegarhq.Sober": {Label: "Sober", Group: "gaming"}},
		Services: map[string]setupOption{"audio": {Label: "Audio", Scope: "user"}},
	}, selection: selection{}}
	m.prepare()
	for i := range m.rows {
		m.rows[i].checked = true
	}
	next, command := m.Update(tea.KeyMsg{Type: tea.KeyEnter})
	result := next.(model)
	if result.stage != 5 || command == nil || !contains(result.selection.Flatpaks, "org.vinegarhq.Sober") || !contains(result.selection.Services, "audio") {
		t.Fatalf("setup selections lost before preview: %+v", result.selection)
	}
}

func TestBackupNeedsSelectionPreviewAndExplicitRestoreAction(t *testing.T) {
	m := model{stage: 5}
	next, command := m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'u'}})
	m = next.(model)
	if m.stage != 6 || command == nil || m.done {
		t.Fatal("backup key did not open the chooser")
	}
	next, _ = m.Update(backupsMsg{choices: []backupChoice{{ID: "20260101T000000Z", Count: 1}}})
	m = next.(model)
	next, command = m.Update(tea.KeyMsg{Type: tea.KeyEnter})
	m = next.(model)
	if m.stage != 7 || command == nil || m.done {
		t.Fatal("choosing a backup must only open its preview")
	}
	next, _ = m.Update(previewMsg{content: "preview"})
	m = next.(model)
	next, _ = m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{'a'}})
	m = next.(model)
	if m.done {
		t.Fatal("config application key triggered a restore from backup preview")
	}
	next, _ = m.Update(tea.KeyMsg{Type: tea.KeyEnter})
	m = next.(model)
	if !m.done || m.action != "u" || m.backupID != "20260101T000000Z" {
		t.Fatal("explicit backup action was lost")
	}
}

func TestEmptyBackupChooserDoesNotStartRestore(t *testing.T) {
	m := model{stage: 6}
	next, command := m.Update(tea.KeyMsg{Type: tea.KeyEnter})
	m = next.(model)
	if m.done || command != nil || m.stage != 6 {
		t.Fatal("empty backup chooser started a restore")
	}
}

func TestPreviewCanScrollThroughLongRequirementLines(t *testing.T) {
	m := model{stage: 5, height: 20, width: 40, preview: strings.Repeat("package [missing] ", 20)}
	for range 3 {
		next, _ := m.Update(tea.KeyMsg{Type: tea.KeyDown})
		m = next.(model)
	}
	if m.scroll != 3 {
		t.Fatal("wrapped requirements cannot be scrolled into view")
	}
}
