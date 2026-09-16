import os
import re

# Directory to search
BASE_DIR = r"c:\Users\fmbuk\OneDrive\Desktop\mon app"

# Regex patterns for Tailwind Gradients and colors
gradient_patterns = [
    # Backgrounds for buttons usually: bg-gradient-to-r from-blue-600 to-indigo-600
    (r'bg-gradient-to-[a-z]+\s+from-(blue|indigo|purple)-[56]00\s+to-(indigo|purple|blue)-[56]00', r'bg-medical-blue hover:bg-medical-dark'),
    (r'bg-gradient-to-[a-z]+\s+from-(blue|indigo|purple)-[67]00\s+to-(indigo|purple|blue)-[67]00', r'bg-medical-blue hover:bg-medical-dark'),
    # Hover states for gradients
    (r'hover:from-(blue|indigo|purple)-[67]00\s+hover:to-(indigo|purple|blue)-[67]00', r'hover:bg-medical-dark'),
    # Text gradients
    (r'bg-clip-text\s+text-transparent\s+bg-gradient-to-[a-z]+\s+from-[a-z]+-[0-9]+\s+to-[a-z]+-[0-9]+', r'text-medical-blue'),
    # Subtle card backgrounds
    (r'bg-gradient-to-[a-z]+\s+from-blue-50\s+to-indigo-50', r'bg-medical-light/20'),
    (r'bg-gradient-to-[a-z]+\s+from-indigo-50\s+to-white', r'bg-white'),
    (r'bg-gradient-to-[a-z]+\s+from-gray-50\s+to-white', r'bg-white'),
    # other specific ones
    (r'bg-gradient-to-[a-z]+\s+from-gray-50\s+to-emerald-50/30', r'bg-medical-light/10 border-medical-light/50'),
    (r'bg-gradient-to-[a-z]+\s+from-gray-50\s+to-gray-100', r'bg-gray-50'),
    # Specific colors to remove/replace
    (r'text-indigo-[567]00', r'text-medical-blue'),
    (r'text-purple-[567]00', r'text-medical-blue'),
    (r'bg-indigo-[567]00', r'bg-medical-blue'),
    (r'bg-purple-[567]00', r'bg-medical-blue'),
    (r'ring-indigo-[567]00', r'ring-medical-blue'),
    (r'focus:border-indigo-[567]00', r'focus:border-medical-blue'),
    (r'focus:ring-indigo-[567]00', r'focus:ring-medical-blue'),
    (r'border-indigo-[2345]00', r'border-medical-blue/30'),
]

# Emojis to replace with Tabler Icons (or empty)
emoji_replacements = {
    "✅": '<i class="ti ti-check"></i>',
    "🚀": '<i class="ti ti-rocket"></i>',
    "💊": '<i class="ti ti-pill"></i>',
    "🏥": '<i class="ti ti-building-hospital"></i>',
    "👨‍⚕️": '<i class="ti ti-stethoscope"></i>',
    "👩‍⚕️": '<i class="ti ti-stethoscope"></i>',
    "👨⚕️": '<i class="ti ti-stethoscope"></i>',
    "👩⚕️": '<i class="ti ti-stethoscope"></i>',
    "⚕️": '<i class="ti ti-medical-cross"></i>',
    "⭐": '<i class="ti ti-star-filled text-yellow-400"></i>',
    "⚠️": '<i class="ti ti-alert-triangle"></i>',
    "❌": '<i class="ti ti-x"></i>',
    "📅": '<i class="ti ti-calendar"></i>',
    "🕒": '<i class="ti ti-clock"></i>',
    "⏰": '<i class="ti ti-clock"></i>',
    "💰": '<i class="ti ti-currency-euro"></i>',
    "💶": '<i class="ti ti-currency-euro"></i>',
    "💵": '<i class="ti ti-currency-euro"></i>',
    "📄": '<i class="ti ti-file-text"></i>',
    "📝": '<i class="ti ti-file-text"></i>',
    "🔍": '<i class="ti ti-search"></i>',
    "🔎": '<i class="ti ti-search"></i>',
    "⚙️": '<i class="ti ti-settings"></i>',
    "🔒": '<i class="ti ti-lock"></i>',
    "🔓": '<i class="ti ti-lock-open"></i>',
    "👤": '<i class="ti ti-user"></i>',
    "🧑": '<i class="ti ti-user"></i>',
    "👥": '<i class="ti ti-users"></i>',
    "📊": '<i class="ti ti-chart-bar"></i>',
    "📈": '<i class="ti ti-trending-up"></i>',
    "🩺": '<i class="ti ti-stethoscope"></i>',
    "💉": '<i class="ti ti-vaccine"></i>',
    "🚑": '<i class="ti ti-ambulance"></i>',
    "💻": '<i class="ti ti-device-laptop"></i>',
    "📱": '<i class="ti ti-device-mobile"></i>',
    "👨‍💻": '<i class="ti ti-user-code"></i>',
    "👨💻": '<i class="ti ti-user-code"></i>',
    "➡️": '<i class="ti ti-arrow-right"></i>',
    "➔": '<i class="ti ti-arrow-right"></i>',
    "➜": '<i class="ti ti-arrow-right"></i>',
    "⬅️": '<i class="ti ti-arrow-left"></i>',
    "🔙": '<i class="ti ti-arrow-left"></i>',
    "👋": '',
    "🎉": '',
    "✨": '',
    "💡": '<i class="ti ti-bulb"></i>',
    "🔔": '<i class="ti ti-bell"></i>',
    "🔥": '',
    "🤝": '<i class="ti ti-friends"></i>',
    "🛡️": '<i class="ti ti-shield-check"></i>',
    "🧠": '<i class="ti ti-brain"></i>',
    "🤖": '<i class="ti ti-robot"></i>',
    "🌿": '<i class="ti ti-leaf"></i>',
    "💬": '<i class="ti ti-message"></i>',
    "👁️": '<i class="ti ti-eye"></i>',
    "📞": '<i class="ti ti-phone"></i>',
    "📌": '<i class="ti ti-pin"></i>',
    "📍": '<i class="ti ti-map-pin"></i>',
    "➕": '<i class="ti ti-plus"></i>',
    "➖": '<i class="ti ti-minus"></i>',
    "👍": '<i class="ti ti-thumb-up"></i>',
    "👎": '<i class="ti ti-thumb-down"></i>',
    "ℹ️": '<i class="ti ti-info-circle"></i>',
    "❓": '<i class="ti ti-help"></i>',
    "❤️": '<i class="ti ti-heart text-red-500"></i>',
    "👨‍👩‍👧‍👦": '<i class="ti ti-users"></i>',
    "🧪": '<i class="ti ti-flask"></i>',
    "🔬": '<i class="ti ti-microscope"></i>',
    "🩹": '<i class="ti ti-bandage"></i>',
    "🩸": '<i class="ti ti-droplet text-red-500"></i>',
    "📋": '<i class="ti ti-clipboard-list"></i>',
    "💳": '<i class="ti ti-credit-card"></i>',
    "📥": '<i class="ti ti-inbox"></i>',
    "📤": '<i class="ti ti-upload"></i>',
}

# Text Replacements (Over-enthusiastic text)
text_replacements = [
    (r"Bienvenue sur votre incroyable plateforme de santé nouvelle génération\s*!", r"Bienvenue sur votre espace santé."),
    (r"Incroyable plateforme", r"Plateforme de santé"),
    (r"nouvelle génération", r""),
    (r"révolutionnaire", r"innovant"),
    (r"le meilleur de la technologie", r"une technologie fiable"),
    (r"!!!+", r"!"),
]

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            original_content = content
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    # Replace gradients and colors
    for pattern, replacement in gradient_patterns:
        content = re.sub(pattern, replacement, content)

    # Replace emojis
    for emoji, replacement in emoji_replacements.items():
        content = content.replace(emoji, replacement)

    # Regex to remove remaining unmapped emojis (matches most common emojis and pictographs)
    # We will exclude numbers and standard symbols.
    emoji_pattern = re.compile(
        r'['
        r'\U0001F600-\U0001F64F'  # Emoticons
        r'\U0001F300-\U0001F5FF'  # Misc Symbols and Pictographs
        r'\U0001F680-\U0001F6FF'  # Transport and Map
        r'\U0001F700-\U0001F77F'  # Alchemical Symbols
        r'\U0001F780-\U0001F7FF'  # Geometric Shapes Extended
        r'\U0001F800-\U0001F8FF'  # Supplemental Arrows-C
        r'\U0001F900-\U0001F9FF'  # Supplemental Symbols and Pictographs
        r'\U0001FA70-\U0001FAFF'  # Symbols and Pictographs Extended-A
        r']+', flags=re.UNICODE)
    
    content = emoji_pattern.sub('', content)

    # Replace texts
    for pattern, replacement in text_replacements:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filepath}")

if __name__ == "__main__":
    for root, dirs, files in os.walk(BASE_DIR):
        if 'venv' in root or '.git' in root or 'node_modules' in root:
            continue
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                process_file(filepath)
    print("Done cleaning templates.")
