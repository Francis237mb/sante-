# -*- coding: utf-8 -*-
"""
Moteur Médical de Fransick Santé
Ce module implémente une base de connaissances médicales approfondie et un moteur de traitement du langage naturel (NLP)
capable d'analyser, synthétiser et générer des réponses médicales précises, variées et personnalisées aux questions de santé.
"""

import random
import re

# ================= SALUTATIONS & PROTOCOLE CONVERSATIONNEL ================= #
GREETING_KEYWORDS = ['bonjour', 'salut', 'hello', 'bonsoir', 'coucou', 'hey', 'bon week-end', 'ça va', 'ca va']
IDENTITY_KEYWORDS = ['qui es tu', 'qui es-tu', 'comment tu tappelles', "comment tu t'appelles", 'tu es qui', 'ton nom', 'tes fonctions', 'que sais tu faire', 'tu fais quoi', 'aide moi', 'aide-moi']
THANKS_KEYWORDS = ['merci', 'remerci', 'thanks', 'au revoir', 'a bientot', 'à bientôt', 'bonne journée', 'super', 'parfait', 'gg']

GREETING_RESPONSES = [
    "**Bonjour ! Je suis l'Assistant Médical Fransick**, votre interlocuteur de santé disponible 24h/24 et 7j/7.\n\nComment vous sentez-vous aujourd'hui ? Je suis à votre disposition pour examiner vos symptômes, vous conseiller sur des posologies ou vous orienter vers nos praticiens.",
    "**Bonjour et ravi de vous accueillir sur votre espace santé Fransick.**\n\nJe suis spécialisé en orientation médicale et pharmacologique. Quel symptôme, résultat ou traitement souhaitez-vous aborder aujourd'hui ?",
    "**Bienvenue sur Fransick Santé.**\n\nMon rôle est de vous fournir des informations médicales précises, fiables et personnalisées. De quoi souhaitez-vous me faire part (symptômes, doutes sur un médicament, conseils de prévention) ?",
    "**Bonjour à vous.** Je suis l'Assistant Médical Fransick. Votre santé et votre sérénité sont notre priorité.\n\nQuelle question médicale souhaitez-vous aborder ?"
]

IDENTITY_RESPONSES = [
    "**Présentation de l'Assistant Médical Fransick**\n\nJe suis le système d'orientation médicale intégré à la plateforme **Fransick Santé**. Mon architecture s'appuie sur les recommandations cliniques internationales pour vous offrir :\n\n• **L'analyse d'orientation symptomatique :** Explications sur vos douleurs et troubles courants.\n• **Le guide pharmacologique :** Posologies de base, contre-indications et interactions médicamenteuses usuelles.\n• **L'assistance au triage médical :** Identification des situations nécessitant une consultation de médecine générale, de spécialiste ou les urgences vitales (SAMU).\n• **Disponibilité 24/7 :** Un suivi ponctuel ou continu pour vous guider.\n\n*Comment puis-je vous aider aujourd'hui ?*",
]

THANKS_RESPONSES = [
    "**Je vous en prie.** Ce fut un plaisir de vous renseigner.\n\nPrenez bien soin de vous et de vos proches. N'hésitez pas à revenir au moindre changement de situation, ou à réserver une consultation avec un médecin sur **Fransick**.",
    "**A votre service.** Votre bien-être est au cœur de la mission de Fransick Santé.\n\nPassez une excellente journée et restez à l'écoute de votre santé. Je reste accessible 24/7 en cas de nouvelle interrogation.",
]


# ================= ENCYCLOPÉDIE CLINIQUE & TAXONOMIE DES SPÉCIALITÉS ================= #
MEDICAL_KNOWLEDGE_BASE = {
    "cardiologie": {
        "keywords": ["cœur", "coeur", "tension", "hypertension", "hypotension", "palpitation", "infarctus", "cardio", "poitrine", "essouffle", "essoufflement", "pouls", "tachycardie", "cholestérol", "cholesterol", "arret cardiaque"],
        "title": "Cardiologie & Système Vasculaire",
        "intro": [
            "L'examen de la sphère cardiovasculaire requiert une extrême vigilance, en particulier face aux variations de tension ou aux palpitations.",
            "Voici les éléments cliniques essentiels concernant le système cardio-vasculaire et vos symptômes."
        ],
        "advice": (
            "**Normes & Objectifs Cliniques :**\n"
            "• Une tension artérielle standard chez l'adulte au repos est d'environ **120/80 mmHg**. Au-delà de 140/90 mmHg constatés à plusieurs reprises, on évoque une hypertension artérielle (HTA).\n"
            "• Le rythme cardiaque normal oscille entre 60 et 100 battements par minute au repos.\n\n"
            "**Mesures Hygiéno-Diététiques recommandées :**\n"
            "• **Réduction sodée :** Limitez l'apport en sel à moins de 5g/jour (évitez les plats industriels et charcuteries).\n"
            "• **Hydratation & Repos :** Privilégiez une activité physique régulière d'endurance (marche 30 min/jour) et des techniques de gestion du stress.\n\n"
            "**Rappel pharmacologique :** Ne suspendez jamais un traitement antihypertenseur ou cardiologique sans l'avis préalable de votre médecin."
        ),
        "red_flags": "[URGENCE VITALE] Toute douleur oppressante au milieu de la poitrine irradiant dans le bras gauche, la mâchoire ou associée à des sueurs froides est une suspicion d'infarctus. Appelez immédiatement le SAMU (15 ou 112)."
    },
    "neurologie": {
        "keywords": ["tête", "mal de tete", "mal de tête", "migraine", "vertige", "malaise", "évanouissement", "evanouissement", "nerf", "céphalée", "cephalee", "fourmillement", "tremblement", "paralysie", "neurologie"],
        "title": "Neurologie & Céphalées",
        "intro": [
            "Les maux de tête (céphalées) et vertiges ont des origines variées : tension vasculaire, fatigue oculaire, déshydratation ou stress neurovégétatif.",
            "Voici une orientation clinique pour comprendre et soulager vos symptômes céphaliques ou neurologiques."
        ],
        "advice": (
            "**Protocole d'Apaisement (Migraines & Céphalées) :**\n"
            "• **Isolement sensoriel :** Allongez-vous dans une pièce calme, sombre et fraîche. Éloignez les écrans lumineux.\n"
            "• **Thérapie thermique :** Appliquez une compresse froide sur le front et les tempes pour provoquer une vasoconstriction analgésique.\n"
            "• **Hydratation immédiate :** Buvez un grand verre d'eau tempérée (la déshydratation est une cause fréquente de céphalée banale).\n\n"
            "**Traitement Analgésique de première intention :**\n"
            "• **Paracétamol :** 1000 mg (adulte de plus de 50 kg), à espacer de 6 heures minimum (max 4g/jour).\n"
            "• **Ibuprofène (200 à 400 mg) :** Efficace sur l'inflammation migraineuse (toujours prendre au cours d'un repas, contre-indiqué en cas de grossesse ou d'ulcère)."
        ),
        "red_flags": "[URGENCE] Si le mal de tête est d'apparition brutale comme un coup de tonnerre, s'accompagne d'un trouble de la parole, d'une faiblesse d'un côté du corps ou d'une raideur de la nuque avec fièvre, consultez le SAMU immédiatement."
    },
    "gastro": {
        "keywords": ["estomac", "vomir", "vomissement", "nausée", "nausee", "diarrhée", "diarrhee", "gastro", "constipation", "ventre", "foie", "ulcère", "ulcere", "reflux", "acidité", "acidite", "aigreur", "crampe abdominale", "ballonnement", "digestion", "colon"],
        "title": "Gastro-Entérologie & Digestion",
        "intro": [
            "Les troubles du tractus gastro-intestinal (nausées, spasmes, altération du transit) nécessitent de mettre le système digestif au repos tout en évitant la déshydratation.",
            "Voici les conseils diététiques et thérapeutiques adaptés à vos symptômes digestifs."
        ],
        "advice": (
            "**Protocole Alimentaire d'Urgence (Régime BRAT) :**\n"
            "• **A consommer :** Riz blanc bien cuit et son eau de cuisson, bananes mûres, compote de pommes sans sucre et pain blanc grillé.\n"
            "• **A proscrire :** Produits laitiers, aliments gras ou frits, épices, café et alcools pendant au moins 48 heures.\n\n"
            "**Réhydratation Fractionnée :**\n"
            "• En cas de diarrhées ou vomissements, buvez de petites gorgées fréquentes d'eau ou de bouillon pour compenser la perte en électrolytes.\n\n"
            "**Support Thérapeutique :**\n"
            "• **Antispasmodique (Phloroglucinol / Spasfon) :** 2 comprimés jusqu'à 3 fois par jour pour calmer les spasmes abdominaux.\n"
            "• **Anti-acides ou Pansements gastriques :** Utilisables si sensation de brûlure rétrosternale ou de reflux (après les repas)."
        ),
        "red_flags": "[CONSULTATION REQUISE] En cas de présence de sang dans les selles ou les vomissements, d'arrêt complet des gaz et du transit avec douleur aiguë, ou de fièvre persistant plus de 3 jours."
    },
    "orl_pneumo": {
        "keywords": ["toux", "rhume", "grippe", "gorge", "angine", "bronchite", "nez", "sinusite", "oreille", "otite", "respiration", "asthme", "mucus", "crachat", "mouchage"],
        "title": "Pneumologie & ORL",
        "intro": [
            "Les affections respiratoires et ORL fréquentes (toux, rhume, maux de gorge) sont majoritairement d'origine virale et demandent principalement un traitement symptomatique et du repos.",
            "Voici le plan d'action pour soulager vos voies respiratoires."
        ],
        "advice": (
            "**Soins Locaux & Hygiène :**\n"
            "• **Lavage Nasal :** Effectuez des lavages réguliers des fosses nasales avec du sérum physiologique ou un spray d'eau de mer hypertonique 3 à 4 fois par jour.\n"
            "• **Inhalation & Humidification :** L'inhalation de vapeur tiède aide à fluidifier les sécrétions et à dégager les bronches.\n"
            "• **Apaisement Pharyngé :** Une boisson tiède avec une cuillère de miel pur adoucit l'irritation pharyngée (rappel : le miel est strictement interdit aux nourrissons < 1 an).\n\n"
            "**Rappel sur les Antibiotiques :**\n"
            "• Les antibiotiques sont inefficaces contre les virus du rhume ou de la grippe. Seul un diagnostic médical en consultation permet de confirmer l'indication d'une antibiotothérapie."
        ),
        "red_flags": "[ATTENTION] Consultez un médecin si vous éprouvez une gêne respiratoire forte (essoufflement, sifflements), si la fièvre dépasse 39°C ou si une toux grasse persiste au-delà de 10 jours."
    },
    "rhumatologie": {
        "keywords": ["dos", "lombaire", "sciatique", "articulation", "arthrose", "arthrite", "genou", "hanche", "muscle", "courbature", "entorse", "tendinite", "fracture", "torticolis", "cervicale"],
        "title": "Rhumatologie, Muscles & Squelette",
        "intro": [
            "Les douleurs ostéo-articulaires et musculaires peuvent provenir d'un traumatisme, d'une sollicitation excessive ou d'une inflammation chronique.",
            "Voici les recommandations adaptées pour apaiser vos articulations et muscles."
        ],
        "advice": (
            "**Protocole Glace vs Chaleur :**\n"
            "• **Application de FROID (Glace) :** Dans les 48h suivant un traumatisme aigu (entorse, choc, gonflement). Le froid limite l'œdème et engourdit la douleur (20 min, 3x/jour, sans contact direct sur la peau).\n"
            "• **Application de CHAUD :** En cas de contracture musculaire, torticolis ou douleur lombaire chronique sans traumatisme brutal. La chaleur favorise la décontraction musculaire.\n\n"
            "**Le Protocole GREC (pour les entorses) :**\n"
            "• **G**lace, **R**epos de l'articulation, **E**lévation du membre, **C**ompression modérée.\n\n"
            "**Analgésiques :** Le paracétamol en première intention, ou l'utilisation ponctuelle d'un gel anti-inflammatoire local en massage doux, peuvent soulager les douleurs banales."
        ),
        "red_flags": "[URGENCE] En cas d'impossibilité totale de prendre appui, d'une déformation visible de l'articulation (suspicion de fracture/luxation) ou de perte de sensibilité nerveuse, consultez immédiatement un service d' urgences."
    },
    "gynecologie_urologie": {
        "keywords": ["règle", "regle", "bas-ventre", "bas ventre", "dysménorrhée", "dysmenorrhee", "grossesse", "enceinte", "ovaire", "kyste", "urinaire", "cystite", "brûlure urinaire", "brulure urinaire", "rein", "pilule", "contraception", "spasfon"],
        "title": "Gynécologie & Urologie",
        "intro": [
            "Le suivi des cycles menstruels, des douleurs pelviennes et de l'appareil urinaire fait appel à des protocoles spécifiques d'apaisement.",
            "Voici la fiche clinique de premier niveau concernant les symptômes pelviens et urinaires."
        ],
        "advice": (
            "**Gestion des Douleurs Menstruelles :**\n"
            "• **Antispasmodique (Phloroglucinol) :** 2 comprimés au moment de la douleur, jusqu'à 3 fois par jour, pour détendre les fibres musculaires de l'utérus.\n"
            "• **AINS (Ibuprofène 200 à 400mg) :** Action rapide sur les prostaglandines responsables des crampes (à prendre lors d'un repas, interdit en cas de grossesse ou d'ulcère).\n"
            "• **Chaleur :** Une bouillotte sur le bas-ventre procure une détente antalgique complémentaire.\n\n"
            "**Prévention et gêne urinaire (Cystite légère) :**\n"
            "• **Hydratation importante :** Buvez au moins 2 litres d'eau par jour pour rincer la vessie.\n"
            "• **Jus de canneberge (Cranberry) :** Peut limiter la fixation de certaines bactéries sur la paroi vésicale.\n"
            "• **Hygiène urinaire :** Ne retenez pas vos urines et pensez à vider votre vessie régulièrement ainsi qu'après chaque rapport sexuel."
        ),
        "red_flags": "[CONSULTATION RAPIDE] En cas de brûlure urinaire accompagnée de fièvre, de frissons ou de douleurs dans le bas du dos (suspicion de pyélonéphrite), consultez rapidement un médecin."
    },
    "pediatrie": {
        "keywords": ["bébé", "bebe", "enfant", "nourrisson", "pédiatre", "pediatre", "fièvre bébé", "fievre bebe", "pleurs", "croissance", "varicelle", "bronchiolite", "vaccin enfant"],
        "title": "Pédiatrie & Soins de l'Enfant",
        "intro": [
            "L'organisme d'un nourrisson ou d'un jeune enfant requiert des dosages médicamenteux basés rigoureusement sur le poids corporel exact.",
            "Voici les repères indispensables pour veiller à la sécurité et au confort de l'enfant."
        ],
        "advice": (
            "**Règle des Posologies Pédiatriques (Paracétamol) :**\n"
            "• Le dosage du Paracétamol est strictement de **15 mg par kilo de poids corporel** par prise, à espacer d'au moins **6 heures** (soit un maximum de 4 prises en 24h, pour 60 mg/kg/jour au total).\n"
            "• *Exemple :* Pour un enfant de 10 kg, la dose est de 150 mg par prise. Utilisez systématiquement la pipette graduée en kilogrammes fournie avec le sirop.\n"
            "• **Mise en garde stricte :** Ne donnez jamais d'aspirine à un enfant ou un adolescent présentant une infection virale ou de la fièvre (risque de Syndrome de Reye).\n\n"
            "**Gestes d'apaisement d'un enfant fébrile :**\n"
            "• Découvrez l'enfant sans le vêtir excessivement (vêtements légers en coton).\n"
            "• Maintenez une température ambiante confortable dans la chambre (18°C à 19°C).\n"
            "• Proposez-lui très fréquemment à boire pour prévenir la déshydratation liée à la transpiration et à la fièvre."
        ),
        "red_flags": "[URGENCE PÉDIATRIQUE] Toute fièvre chez un nourrisson de moins de 3 mois, un comportement anormalement amorphe, un refus de s'alimenter ou de boire de plus de 6 heures, ou l'apparition de taches cutanées violacées ne s'effaçant pas à la pression exigent une prise en charge médicale urgente."
    },
    "dermatologie": {
        "keywords": ["bouton", "peau", "démangeaison", "demangeaison", "allergie", "plaie", "urticaire", "eczéma", "eczema", "acné", "acne", "mycose", "brûlure", "brulure", "éruption", "eruptin", "gonflement"],
        "title": "Dermatologie & Allergie",
        "intro": [
            "La peau est le premier organe de protection du corps humain ; toute éruption, piqûre ou rougeur mérite des soins hygiéniques doux.",
            "Voici les premières indications d'apaisement cutané."
        ],
        "advice": (
            "**Soins Cutanés & Hygiène :**\n"
            "• **Eviter le grattage :** Ne grattez pas une zone irritée ou une lésion cutanée pour empêcher les risques de surinfection bactérienne (impétigo) et de cicatrices définitives.\n"
            "• **Nettoyage :** Utilisez un nettoyant doux (pain surgras, gel sans savon pH neutre) plutôt qu'un savon agressif.\n\n"
            "**Orientations Symptomatiques :**\n"
            "• *Pour une plaie légère ou rougeur superficielle :* Rincez sous l'eau potable, désinfectez avec un antiseptique aqueux doux et appliquez une crème protectrice ou cicatrisante.\n"
            "• *Pour une réaction prurigineusement légère (urticaire ponctuelle, piqûre d'insecte) :* Un traitement antihistaminique par voie orale (en pharmacie) peut calmer rapidement les démangeaisons."
        ),
        "red_flags": "[URGENCE ALLERGIQUE] Si l'éruption cutanée ou le gonflement s'accompagne d'un œdème des lèvres, de la langue ou de difficultés respiratoires (œdème de Quincke), contactez le SAMU (15 ou 112) immédiatement."
    },
    "endocrino_metabolisme": {
        "keywords": ["diabète", "diabete", "glycémie", "glycemie", "sucre", "insuline", "thyroïde", "thyroide", "poids", "obésité", "obesite", "maigrir", "hypoglycémie"],
        "title": "Endocrinologie, Métabolisme & Nutrition",
        "intro": [
            "Le système endocrinien régule l'équilibre hormonal, le métabolisme glucidique (glycémie) et les fonctions énergétiques globales.",
            "Voici les repères médicaux essentiels pour la gestion de vos équilibres métaboliques."
        ],
        "advice": (
            "**Equilibre Glycémique (Diabète) :**\n"
            "• Une glycémie à jeun normale se situe entre **0,70 et 1,10 g/L** (3,9 à 6,1 mmol/L). Un diagnostic de diabète se base sur une glycémie à jeun > 1,26 g/L constatée à deux reprises.\n\n"
            "**Gestion d'une Hypoglycémie Aiguë (< 0,70 g/L ou malaise sucré) :**\n"
            "• *Symptômes typiques :* Sueurs froides, tremblements, palpitations, sensation de faim intense, vertiges.\n"
            "• *Action immédiate :* Consommez environ 15g de sucre rapide (3 morceaux de sucre ou un verre de jus de fruit pur). Attendez 15 minutes avant d'évaluer la récupération, puis consommez un féculent ou pain pour maintenir la glycémie stable.\n\n"
            "**Hygiène nutritionnelle :** Une alimentation variée, riche en fibres (légumes, céréales complètes) aide à lisser l'absorption du glucose et des lipides dans l'organisme."
        ),
        "red_flags": "[IMPORTANT] N'ajustez jamais seuls vos dosages de traitements hormonaux, antidiabétiques oraux ou d'insuline sans la validation officielle de votre médecin traitant ou spécialiste."
    },
    "pharmacologie_posologie": {
        "keywords": ["paracetamol", "doliprane", "ibuprofene", "amoxicilline", "amoxi", "augmentin", "antibiotique", "efferalgan", "dafalgan", "aspirine", "posologie", "effets secondaires", "médicament", "medicament", "ordonnance", "dose"],
        "title": "Pharmacologie & Posologies",
        "intro": [
            "La sécurité médicamenteuse repose sur le respect scrupuleux des doses indiquées, des intervalles entre les prises et du respect des contre-indications.",
            "Voici un récapitulatif des principes de sécurité concernant les traitements d'usage courant."
        ],
        "advice": (
            "**Paracétamol (Doliprane, Dafalgan, Efferalgan) :**\n"
            "• **Posologie Adulte :** 500 mg à 1000 mg (1 g) par prise, avec un intervalle **d'au moins 4 à 6 heures** entre deux prises.\n"
            "• **Dose maximale absolue :** **4 000 mg (4 g) par 24 heures** chez l'adulte de plus de 50 kg sans pathologie hépatique. Le dépassement de ce plafond est toxique pour le foie.\n\n"
            "**Anti-inflammatoires Non Stéroïdiens (AINS : Ibuprofène) :**\n"
            "• À prendre **au cours d'un repas** pour protéger la muqueuse gastrique.\n"
            "• **Contre-indications majeures :** Interdits chez la femme enceinte à partir du 6ème mois (et déconseillés avant), ainsi que chez les patients sous anticoagulants ou souffrant d'ulcère.\n\n"
            "**Les Antibiotiques :**\n"
            "• Ils sont délivrés strictement sur prescription médicale. Il est impératif de suivre le traitement jusqu'à sa date de fin prévue par l'ordonnance, même si les symptômes ont disparu au bout de quelques jours, pour ne pas favoriser la résistance bactérienne."
        ),
        "red_flags": "[ALERTE INDÉSIRABLE] En cas d'apparition soudaine d'effets secondaires suspectés (éruption cutanée naissante, nausées fortes après prise d'un nouveau médicament), interrompez immédiatement la prise et consultez un praticien."
    },
    "sante_mentale_sommeil": {
        "keywords": ["stress", "anxiété", "anxiete", "angoisse", "dépression", "depression", "triste", "panique", "insomnie", "sommeil", "burnout", "fatigue morale", "somnifère", "somnifere"],
        "title": "Santé Mentale & Sommeil",
        "intro": [
            "La santé mentale et la régularité du sommeil sont essentielles pour le maintien de l'immunité, de la mémoire et de l'équilibre de l'organisme.",
            "Voici des repères hygiéniques et relaxants pour apaiser le stress et améliorer la qualité de vos nuits."
        ],
        "advice": (
            "**Technique de Relaxation : La Cohérence Cardiaque :**\n"
            "• En cas d'anxiété passagère ou d'accélération cardiaque liée au stress : installez-vous dans un endroit calme au repos.\n"
            "• **Inspirez par le nez pendant 5 secondes**, puis **expirez doucement par la bouche pendant 5 secondes**.\n"
            "• Répétez cet exercice pendant 5 minutes. Il contribue à diminuer le taux de cortisol et à calmer le système nerveux.\n\n"
            "**Hygiène du Sommeil :**\n"
            "• **Réduction lumineuse :** Éloignez les écrans d'ordinateur ou de téléphone au moins 45 minutes avant l'heure de couchage.\n"
            "• **Ambiance de repos :** Privilégiez une température tempérée de la chambre (vers 18°C-19°C), au silence et dans l'obscurité."
        ),
        "red_flags": "[SOUTIEN PROFONDEUR] En cas d'anxiété continue ou d'épuisement moral persistant, il est primordial d'échanger avec un médecin ou un psychologue diplômé en toute discrétion afin de mettre en place une aide adaptée."
    }
}


def analyze_and_generate_response(user_message, chat_history_list=None):
    """
    Moteur IA Médical de Fransick
    Analyse le message de l'utilisateur par recherche lexicale et sémantique de premier niveau,
    puis renvoie une réponse médicale structurée au format Markdown au style soigné.
    """
    text = user_message.strip()
    text_lower = text.lower()
    
    # 1. Vérification des salutations et messages d'introduction simples
    is_short = len(text) <= 35
    has_greeting = any(re.search(r'\b' + re.escape(g) + r'\b', text_lower) for g in GREETING_KEYWORDS)
    has_identity = any(re.search(r'\b' + re.escape(i) + r'\b', text_lower) for i in IDENTITY_KEYWORDS)
    has_thanks = any(re.search(r'\b' + re.escape(t) + r'\b', text_lower) for t in THANKS_KEYWORDS)

    if has_identity:
        return random.choice(IDENTITY_RESPONSES)
    if has_thanks and len(text) <= 50:
        return random.choice(THANKS_RESPONSES)
    if has_greeting and is_short and not any(w in text_lower for w in ['mal', 'douleur', 'symptome', 'symptôme', 'fièvre', 'fievre', 'toux', 'sang', 'médecine', 'médicament']):
        return random.choice(GREETING_RESPONSES)

    # 2. Recherche par domaines cliniques pertinents
    matched_domains = []
    for domain_key, data in MEDICAL_KNOWLEDGE_BASE.items():
        score = 0
        for kw in data["keywords"]:
            if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower) or (len(kw) > 4 and kw.lower() in text_lower):
                score += 1
        if score > 0:
            matched_domains.append((score, domain_key, data))
            
    # Trier par score de pertinence décroissant
    matched_domains.sort(key=lambda x: x[0], reverse=True)

    if matched_domains:
        top_match = matched_domains[0][2]
        intro_sentence = random.choice(top_match["intro"])
        
        response = (
            f"### {top_match['title']}\n\n"
            f"*{intro_sentence}*\n\n"
            f"Suite à votre message : *« {text} »*, voici les éléments de repère cliniques à connaître :\n\n"
            f"{top_match['advice']}\n\n"
            f"___\n"
            f"{top_match['red_flags']}\n\n"
            f"**Note Fransick Santé :** Pour un diagnostic précis, un examen clinique de confirmation ou l'établissement d'une prescription de soins, programmez une consultation (vidéo ou en cabinet) auprès de l'un de nos praticiens."
        )
        return response

    # 3. Réponse d'inférence générale (sans domaine spécialisé directement identifié)
    stop_words = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'ou', 'pour', 'que', 'qui', 'dans', 'sur', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'son', 'sa', 'ses', 'nous', 'vous', 'avec', 'est', 'sont', 'être', 'avoir', 'jai', "j'ai", 'fait', 'plus', 'moins', 'très', 'tres', 'faire', 'tout', 'toute', 'tous', 'bien', 'comme', 'comment', 'quand', 'pourquoi', 'depuis'}
    raw_words = re.findall(r'\b[a-zA-ZàâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]{4,}\b', text)
    meaningful_words = [w for w in raw_words if w.lower() not in stop_words]
    
    topic = ", ".join(meaningful_words[:4]) if meaningful_words else "votre situation"

    dynamic_templates = [
        (
            f"### Évaluation et Orientations : {topic.capitalize()}\n\n"
            f"J'ai pris connaissance de votre message : *« {text} »*.\n\n"
            f"En matière d'investigation concernant **{topic}**, l'évaluation médicale s'attache à comprendre l'intensité des symptômes, leur évolution depuis leur apparition, ainsi que vos éventuels antécédents médicaux.\n\n"
            f"**Conseils d'accompagnement général :**\n"
            f"1. **Observation :** Notez la fréquence de survenue du symptôme et ce qui semble le soulager ou l'accentuer.\n"
            f"2. **Prudence médicamenteuse :** Ne commencez pas un traitement anti-inflammatoire ou antibiotique par vous-même sans avis d'un praticien. Pour les inconforts banals sans gravité, le paracétamol reste généralement recommandé dans le strict respect de la posologie de l'adulte (max 1g par prise et 4g par jour, espacés de 6h).\n"
            f"3. **Hydratation et repos :** Veillez à bien vous hydrater tout au long de la journée avec de l'eau potable.\n\n"
            f"___\n"
            f"[RAPPEL D'URGENCE] En cas d'apparition de signes d'alerte (fièvre > 39°C prolongée, difficultés de respiration ou douleur violente), contactez les services d'urgence médicaux (15 ou 112).\n\n"
            f"**Pour aller plus loin sur Fransick :** Si le symptôme persiste, planifiez facilement un rendez-vous depuis votre espace personnel avec l'un de nos médecins qualifiés pour une consultation d'évaluation."
        ),
        (
            f"### Orientation Médicale : {topic.capitalize()}\n\n"
            f"Voici mon retour d'analyse d'information concernant votre sollicitation : *« {text} »*.\n\n"
            f"L'étude des troubles apparentés à **{topic}** doit s'interpréter globalement de manière progressive et attentive.\n\n"
            f"**Recommandations d'usage :**\n"
            f"• **Surveillance générale :** Évitez tout effort physique excessif ou inconfortable tant que l'origine du symptôme n'a pas été confirmée.\n"
            f"• **Vigilance dans l'automédication :** Ne combinez pas plusieurs médicaments sans avoir échangé au préalable avec un pharmacien ou un médecin traitant.\n"
            f"• **Hydratation :** Consommez de l'eau en petite quantité mais de façon régulière au cours de la journée.\n\n"
            f"___\n"
            f"**Avis Clinique Fransick :** Une orientation virtuelle ne saurait se substituer à une auscultation en règle par un praticien de santé. N'hésitez pas à vous diriger vers le répertoire des médecins sur votre application Fransick afin de réserver un créneau de consultation."
        )
    ]
    
    return random.choice(dynamic_templates)
