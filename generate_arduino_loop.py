"""
Convertit Instruction.txt en code C++ pour la loop() Arduino.

Mapping des pistes (identique au SVG) :
    L  -> WRITING_PINS[0]  (Pos 1)
    R  -> WRITING_PINS[1]  (Pos 2)
    A  -> WRITING_PINS[2]  (Pos 3)
    F  -> WRITING_PINS[3]  (Pos 4)
    B1 -> WRITING_PINS[4]  (Pos 5)  -- barre de début (du début jusqu'à B)
    B2 -> WRITING_PINS[5]  (Pos 6)  -- barre de fin   (de B jusqu'à la fin)

La durée de chaque action est calculée exactement comme dans le script SVG :
    hauteur (cm) = (distance / v_fwd_ou_v_side) * rap
    durée   (ms) = (hauteur / rap) * 1000   ->  simplifiée : (distance / vitesse) * 1000
"""

import sys

# ──────────────────────────────────────────────
# Lecture du fichier d'instructions
# ──────────────────────────────────────────────
file_path = "Instruction.txt"

try:
    with open(file_path, "r") as f:
        lines = [line.strip() for line in f if line.strip() != ""]
except FileNotFoundError:
    sys.exit(f"Erreur : fichier '{file_path}' introuvable.")

# ──────────────────────────────────────────────
# Parsing de l'entête (4 premières lignes)
# ──────────────────────────────────────────────
rap    = float(lines[0])   # ratio cm/s  (pixels par seconde sur le papier)
v_fwd  = float(lines[1])   # vitesse avant/arrière (unités/s)
v_side = float(lines[2])   # vitesse latérale      (unités/s)
marge  = float(lines[3])   # marge initiale (cm)

print(f"# rap={rap}  v_fwd={v_fwd}  v_side={v_side}  marge={marge}")
print()

# ──────────────────────────────────────────────
# Mapping instruction -> index WRITING_PINS
# ──────────────────────────────────────────────
PIN_MAP = {
    "L": 5,   # Pos 1
    "R": 4,   # Pos 2
    "A": 3,   # Pos 3
    "F": 2,   # Pos 4
    # B et P sont traités à part
}  

# ──────────────────────────────────────────────
# Génération des actions
# Format : (pin_index | None, duration_ms | None, label)
# ──────────────────────────────────────────────
actions = []   # liste de dicts

i = 4  # on commence après les 4 variables
while i < len(lines):
    instr = lines[i]

    if instr in ("F", "A", "R", "L"):
        i += 1
        distance = float(lines[i])
        vitesse = v_fwd if instr in ("F", "A") else v_side
        duration_ms = int(round((distance / vitesse) * 1000))
        pin = PIN_MAP[instr]
        actions.append({"type": "move", "pin": pin, "ms": duration_ms, "label": f"{instr} {distance}"})

    elif instr == "B":
        # B : active pin4 (B1) depuis le début, et pin5 (B2) jusqu'à la fin.
        # Dans la simulation on marque juste le point B avec un commentaire ;
        # les deux barres seront gérées en encadrant toute la séquence.
        actions.append({"type": "B", "label": "B"})

    elif instr == "P":
        i += 1
        time_val = float(lines[i])
        duration_ms = int(round(time_val * 1000))
        actions.append({"type": "pause", "ms": duration_ms, "label": f"P {time_val}"})

    i += 1

# ──────────────────────────────────────────────
# Génération du code C++ pour la loop()
# ──────────────────────────────────────────────
cpp_lines = []

def w(line=""):
    cpp_lines.append(line)

w("// ──────────────────────────────────────────────────────────────")
w("// Code généré automatiquement par generate_arduino_loop.py")
w(f"// rap={rap}  v_fwd={v_fwd}  v_side={v_side}  marge={marge}")
w("// ──────────────────────────────────────────────────────────────")
w()
w("void loop() {")
w("  // Attendre l'appui sur le bouton")
w("  while (digitalRead(PUSH_BUTTON) == HIGH) {}")
w("  while (digitalRead(PUSH_BUTTON) == LOW)  {}")
w()
w('  Serial.println("Script start");')
w()

# Trouver si on a un B pour savoir quand l'activer/désactiver
b_index = next((idx for idx, a in enumerate(actions) if a["type"] == "B"), None)

# Pin 4 (B1) : HIGH dès le début, LOW au moment de B
# Pin 5 (B2) : HIGH au moment de B, LOW à la fin
w("  // Barre de début (WRITING_PINS[1]) — active depuis le départ")
w("  digitalWrite(WRITING_PINS[0], HIGH);")
w()

for idx, action in enumerate(actions):

    if action["type"] == "move":
        pin = action["pin"]
        ms  = action["ms"]
        w(f"  // {action['label']}")
        w(f"  digitalWrite(WRITING_PINS[{pin}], HIGH);")
        w(f"  delay({ms});")
        w(f"  digitalWrite(WRITING_PINS[{pin}], LOW);")
        w()

    elif action["type"] == "pause":
        ms = action["ms"]
        w(f"  // {action['label']} (pause)")
        w(f"  delay({ms});")
        w()

    elif action["type"] == "B":
        w("  // B — fin de la barre de début, début de la barre de fin")
        w("  digitalWrite(WRITING_PINS[0], LOW);")
        w("  digitalWrite(WRITING_PINS[1], HIGH);")
        w()

w("  // Fin du script — éteindre la barre de fin")
w("  digitalWrite(WRITING_PINS[1], LOW);")
w('  Serial.println("Script end");')
w("}")

cpp_code = "\n".join(cpp_lines)
print(cpp_code)

# Sauvegarde dans un fichier .ino partiel
output_path = "arduino_loop.ino"
with open(output_path, "w") as f:
    f.write(cpp_code)

print(f"\n// Fichier sauvegardé : {output_path}")
