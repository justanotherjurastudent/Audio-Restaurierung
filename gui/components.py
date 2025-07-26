"""GUI-Komponenten und Layout-Helper"""

from typing import Dict, List, Callable, Any, Optional
import tkinter as tk
import customtkinter as ctk
from .styles import Colors, Fonts, Dimensions, Icons

class ParameterSlider(ctk.CTkFrame):
    """Wiederverwendbarer Slider mit Label und Wert-Anzeige"""
    
    def __init__(self, parent: ctk.CTkFrame, label: str, from_: float, to: float, 
                 initial_value: float, unit: str = "", width: int = Dimensions.SLIDER_WIDTH,
                 help_text: str = "", callback: Optional[Callable] = None):
        super().__init__(parent)
        
        self.callback = callback
        self.unit = unit
        
        # Label
        self.label = ctk.CTkLabel(self, text=label, font=Fonts.LABEL_BOLD())  # ← () HINZUGEFÜGT
        self.label.pack(pady=(10, 3))
        
        # Variable
        self.var = ctk.DoubleVar(value=initial_value)
        
        # Slider
        self.slider = ctk.CTkSlider(self, from_=from_, to=to, variable=self.var, width=width)
        self.slider.pack(pady=3)
        self.slider.configure(command=self._on_change)
        
        # Wert-Label
        self.value_label = ctk.CTkLabel(self, text=f"{initial_value} {unit}", font=Fonts.SMALL_HELP())  # ← () HINZUGEFÜGT
        self.value_label.pack(pady=2)
        
        # Hilfetext
        if help_text:
            self.help_label = ctk.CTkLabel(
                self, 
                text=help_text, 
                font=Fonts.SMALL_HELP(), 
                text_color="gray",
                wraplength=width - 20,  # ✅ Automatischer Textumbruch
                justify="left"  # ✅ Linksbündig für bessere Lesbarkeit
            )
            self.help_label.pack(pady=(0, 15), padx=10, fill="x")
    
    def _on_change(self, value: float) -> None:
        """Wird bei Slider-Änderung aufgerufen"""
        if isinstance(value, str):
            value = float(value)
        
        if self.unit:
            self.value_label.configure(text=f"{value:.1f} {self.unit}")
        else:
            self.value_label.configure(text=f"{value:.1f}")
        
        if self.callback:
            self.callback(value)
    
    def get_value(self) -> float:
        """Gibt den aktuellen Wert zurück"""
        return self.var.get()
    
    def set_value(self, value: float) -> None:
        """Setzt einen neuen Wert"""
        self.var.set(value)
        self._on_change(value)

class IntegerSlider(ctk.CTkFrame):
    """Slider für Integer-Werte"""
    
    def __init__(self, parent: ctk.CTkFrame, label: str, from_: int, to: int, 
                 initial_value: int, help_text: str = "", callback: Optional[Callable] = None):
        super().__init__(parent)
        
        self.callback = callback
        
        # Label
        self.label = ctk.CTkLabel(self, text=label, font=Fonts.LABEL_BOLD())  # ← () HINZUGEFÜGT
        self.label.pack(pady=(10, 3))
        
        # Variable
        self.var = ctk.IntVar(value=initial_value)
        
        # Slider
        self.slider = ctk.CTkSlider(self, from_=from_, to=to, variable=self.var, 
                                   width=Dimensions.SLIDER_WIDTH, number_of_steps=to-from_)
        self.slider.pack(pady=3)
        self.slider.configure(command=self._on_change)
        
        # Wert-Label
        self.value_label = ctk.CTkLabel(self, text=str(initial_value), font=Fonts.SMALL_HELP())  # ← () HINZUGEFÜGT
        self.value_label.pack(pady=2)
        
        # Hilfetext
        if help_text:
            self.help_label = ctk.CTkLabel(self, text=help_text, font=Fonts.SMALL_HELP(), text_color="gray")  # ← () HINZUGEFÜGT
            self.help_label.pack(pady=(0, 15))
    
    def _on_change(self, value: float) -> None:
        """Wird bei Slider-Änderung aufgerufen"""
        int_value = int(float(value))
        self.value_label.configure(text=str(int_value))
        
        if self.callback:
            self.callback(int_value)
    
    def get_value(self) -> int:
        """Gibt den aktuellen Wert zurück"""
        return self.var.get()

class ButtonGrid(ctk.CTkFrame):
    """Grid-Layout für Buttons mit gleichmäßigen Abständen"""
    
    def __init__(self, parent: ctk.CTkFrame):
        super().__init__(parent)
        
        self.grid_frame = ctk.CTkFrame(self)
        self.grid_frame.pack(fill="x", padx=10)
        
        self.buttons: List[ctk.CTkButton] = []
        self.spacers: List[ctk.CTkFrame] = []
    
    def add_button_pair(self, left_button: ctk.CTkButton, right_button: ctk.CTkButton) -> None:
        """Fügt ein Button-Paar mit Spacer hinzu"""
        left_button.pack(side="left", padx=(0, 10))
        
        # Spacer für gleichmäßigen Abstand
        spacer = ctk.CTkFrame(self.grid_frame, width=10, height=1, fg_color="transparent")
        spacer.pack(side="left", expand=True, fill="x")
        self.spacers.append(spacer)
        
        right_button.pack(side="right", padx=(10, 0))
        
        self.buttons.extend([left_button, right_button])

class StatusListBox(ctk.CTkFrame):
    """Listbox mit Status-Icons"""
    
    def __init__(self, parent: ctk.CTkFrame):
        super().__init__(parent)
        
        self.listbox = tk.Listbox(
            self, 
            selectmode=tk.EXTENDED,
            height=6, 
            font=("Arial", 10),
            bg=Colors.LISTBOX_BG, 
            fg=Colors.LISTBOX_FG,
            selectbackground=Colors.LISTBOX_SELECT
        )
        self.listbox.pack(fill="both", expand=True, padx=8, pady=8)
    
    def add_item(self, text: str, status_icon: str = "") -> None:
        """Fügt ein Element zur Liste hinzu"""
        display_text = f"{status_icon} {text}" if status_icon else text
        self.listbox.insert(tk.END, display_text)
    
    def update_item_status(self, index: int, status_icon: str) -> None:
        """Aktualisiert den Status eines Elements"""
        try:
            current_text = self.listbox.get(index)
            
            # Entferne vorhandene Icons
            for icon in [Icons.PROCESSING, Icons.SUCCESS, Icons.ERROR, Icons.CANCELLED]:
                if current_text.startswith(icon + " "):
                    current_text = current_text[2:]
                    break
            
            new_text = f"{status_icon} {current_text}"
            self.listbox.delete(index)
            self.listbox.insert(index, new_text)
        except tk.TclError:
            pass  # Index ungültig
    
    def get_selected_indices(self) -> List[int]:
        """Gibt die ausgewählten Indizes zurück"""
        return list(self.listbox.curselection())
    
    def get_item(self, index: int) -> str:
        """Gibt den Text eines Elements zurück"""
        return self.listbox.get(index)
    
    def delete_item(self, index: int) -> None:
        """Löscht ein Element"""
        self.listbox.delete(index)
    
    def clear(self) -> None:
        """Leert die Liste"""
        self.listbox.delete(0, tk.END)
    
    def size(self) -> int:
        """Gibt die Anzahl der Elemente zurück"""
        return self.listbox.size()

class RadioButtonGroup(ctk.CTkFrame):
    """Gruppe von Radio Buttons"""
    
    def __init__(self, parent: ctk.CTkFrame, options: List[tuple], default_value: str):
        super().__init__(parent)
        
        self.variable = ctk.StringVar(value=default_value)
        self.buttons: Dict[str, ctk.CTkRadioButton] = {}
        
        for value, text, description in options:
            # Radio Button
            radio_btn = ctk.CTkRadioButton(
                self, 
                text=text, 
                variable=self.variable, 
                value=value,
                font=Fonts.BUTTON_SMALL()  # ← () HINZUGEFÜGT
            )
            radio_btn.pack(anchor="w", padx=15, pady=5)
            self.buttons[value] = radio_btn
            
            # Beschreibung
            if description:
                desc_label = ctk.CTkLabel(
                    self, 
                    text=description, 
                    font=Fonts.HELP_TEXT(),  # ← () HINZUGEFÜGT
                    text_color="gray"
                )
                desc_label.pack(anchor="w", padx=35, pady=(0, 8))
    
    def get_value(self) -> str:
        """Gibt den ausgewählten Wert zurück"""
        return self.variable.get()
    
    def set_value(self, value: str) -> None:
        """Setzt einen neuen Wert"""
        self.variable.set(value)
