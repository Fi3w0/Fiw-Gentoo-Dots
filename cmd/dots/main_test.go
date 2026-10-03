package main

import (
	tea "github.com/charmbracelet/bubbletea"
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
