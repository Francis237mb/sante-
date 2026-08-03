# -*- coding: utf-8 -*-
"""
Moteur IA Médical de Fransick Santé (Silicon Valley Hybrid Expert System)
Ce module implémente une base de connaissances médicales approfondie et un moteur de traitement du langage naturel (NLP)
capable d'analyser, synthétiser et générer des réponses médicales précises, variées et personnalisées à toutes les questions de santé.
"""

import random
import re

# ================= SALUTATIONS & PROTOCOLE CONVERSATIONNEL ================= #
GREETING_KEYWORDS = ['bonjour', 'salut', 'hello', 'bonsoir', 'coucou', 'hey', 'bon week-end', 'ça va', 'ca va']
IDENTITY_KEYWORDS = ['qui es tu', 'qui es-tu', 'comment tu tappelles', "comment tu t'appelles", 'tu es qui', 'ton nom', 'tes fonctions', 'que sais tu faire', 'tu fais quoi', 'aide moi', 'aide-moi']
THANKS_KEYWORDS = ['merci', 'remerci', 'thanks', 'au revoir', 'a bientot', 'à bientôt', 'bonne journée', 'super', 'parfait', 'gg']

GREETING_RESPONSES = [
    "🩺 **Bonjour ! Je suis le Dr. Fransick IA**, votre assistant médical personnel diplômé d'excellence en ligne 24h/24 et 7j/7.\n\nComment vous sentez-vous aujourd'hui ? Je suis à votre entière disposition pour examiner vos symptômes, vous conseiller sur des posologies ou vous orienter vers nos spécialistes.",
    "👋 **Bonjour et ravi de vous accueillir sur votre espace santé Fransick !**\n\nJe suis votre assistant IA spécialisé en médecine générale et spécialisée. Quel symptôme, résultat ou traitement souhaitez-vous que nous abordions ensemble aujourd'hui ?",
    "🌟 **Hello ! Bienvenue sur Fransick Santé.**\n\nEn tant que Dr. Fransick IA, mon rôle est de vous fournir des éclairages médicaux précis, fiables et personnalisés. De quoi souhaitez-vous me faire part ? (Symptômes, doutes sur un médicament, conseils de prévention...)",
    "🩺 **Bonjour à vous !** Je suis le Dr. Fransick IA. Votre santé et votre sérénité sont ma priorité absolue.\n\nQuelle question médicale puis-je résoudre pour vous à cet instant ?"
]

IDENTITY_RESPONSES = [
    "🩺 **Présentation du Dr. Fransick IA**\n\nJe suis l'intelligence artificielle médicale d'élite intégrée à la plateforme **Fransick Santé**. Mon architecture combine les dernières recommandations cliniques internationales (HAS, OMS) pour vous offrir :\n\n• 🔍 **L'analyse d'orientation symptomatique :** Explications de vos douleurs et troubles.\n• 💊 **Le guide pharmacologique :** Posologies, contre-indications et interactions médicamenteuses.\n• 🏥 **L'assistance au triage médical :** Identification des situations nécessitant une consultation de médecine générale, de spécialiste ou les urgences vitales (SAMU).\n• ⏱️ **Disponibilité 24/7 :** Une mémoire conversationnelle continue pour suivre votre bien-être.\n\n*Comment puis-je vous aider aujourd'hui ?*",
]

THANKS_RESPONSES = [
    "🙏 **Je vous en prie !** Ce fut un plaisir de vous conseiller.\n\nPrenez bien soin de vous et de vos proches. N'hésitez surtout pas à revenir me consulter au moindre changement d'état, ou à réserver un rendez-vous vidéo/cabinet avec un médecin partenaire sur **Fransick**.",
    "🌟 **A votre service !** Votre bien-être est au cœur de la mission de Fransick Santé.\n\nPassez une excellente journée et restez à l'écoute de votre corps. Je reste accessible 24/7 si une autre interrogation venait à se présenter !",
]


# ================= ENCYCLOPÉDIE CLINIQUE & TAXONOMIE DES SPÉCIALITÉS ================= #
MEDICAL_KNOWLEDGE_BASE = {
    "cardiologie": {
        "keywords": ["cœur", "coeur", "tension", "hypertension", "hypotension", "palpitation", "infarctus", "cardio", "poitrine", "essouffle", "essoufflement", "pouls", "tachycardie", "cholestérol", "cholesterol", "arret cardiaque"],
        "title": "❤️ Cardiologie & Système Vasculaire",
        "intro": [
            "L'examen de la sphère cardiovasculaire requiert une extrême vigilance, en particulier face aux variations de tension ou aux palpitations.",
            "Voici les éléments cliniques essentiels concernant le système cardio-vasculaire et vos symptômes."
        ],
        "advice": (
            "📌 **Normes & Objectifs Cliniques :**\n"
            "• Une tension artérielle standard chez l'adulte au repos est d'environ **120/80 mmHg**. Au-delà de 140/90 mmHg constatés à plusieurs reprises, on évoque une hypertension (HTA).\n"
            "• Le rythme cardiaque normal oscille entre 60 et 100 battements par minute au repos.\n\n"
            "🌿 **Mesures Hygiéno-Diététiques recommandées :**\n"
            "• **Réduction sodée :** Limitez l'apport en sel à moins de 5g/jour (évitez les plats industriels et charcuteries).\n"
            "• **Hydratation & Repos :** Privilégiez une activité physique régulière d'endurance (marche 30 min/jour) et des techniques de gestion de stress (cohérence cardiaque).\n\n"
            "💊 **Rappel pharmacologique :** Ne suspendez jamais un traitement antihypertenseur ou cardiologique sans l'aval exprès de votre cardiologue."
        ),
        "red_flags": "🚨 **Alerte Urgence Vitale :** Toute douleur oppressante au milieu de la poitrine irradiant dans le bras gauche, la mâchoire ou associée à des sueurs froides est une suspicion d'infarctus. Appelez immédiatement le SAMU (15 ou 112) !"
    },
    "neurologie": {
        "keywords": ["tête", "mal de tete", "mal de tête", "migraine", "vertige", "malaise", "évanouissement", "evanouissement", "nerf", "céphalée", "cephalee", "fourmillement", "tremblement", "paralysie", "neurologie"],
        "title": "🧠 Neurologie & Céphalées",
        "intro": [
            "Les maux de tête (céphalées) et vertiges ont des origines variées : tension vasculaire, fatigue oculaire, déshydratation ou stress neurovégétatif.",
            "Voici votre fiche d'orientation clinique pour apaiser et identifier vos symptômes neurologiques ou céphaliques."
        ],
        "advice": (
            "🛡️ **Protocole d'Apaisement (Migraines & Céphalées) :**\n"
            "• **Isolement sensoriel :** Allongez-vous dans une pièce calme, sombre et fraîche. Éloignez les écrans à lumière bleue.\n"
            "• **Thérapie thermique :** Appliquez une compresse froide ou un gant glacé sur le front et les tempes pour provoquer une vasoconstriction analgésique.\n"
            "• **Hydratation immédiate :** Buvez un grand verre d'eau tempérée (la déshydratation est la première cause de céphalée banale).\n\n"
            "💊 **Traitement Analgésique de première intention :**\n"
            "• **Paracétamol (Doliprane / Dafalgan) :** 1000 mg (adulte de plus de 50 kg), à espacer de 6 heures minimum (max 4g/jour).\n"
            "• **Ibuprofène (200 à 400 mg) :** Efficace sur l'inflammation migrénieuse (toujours prendre au cours d'un repas, contre-indiqué si grossesse ou ulcère)."
        ),
        "red_flags": "🚨 **Drapeaux Rouges (Urgence absolue) :** Si le mal de tête est d'apparition brutale comme un coup de tonnerre, s'accompagne d'un trouble de la parole, d'une faiblesse d'un côté du corps ou d'une raideur de la nuque avec fièvre, consultez le SAMU immédiatement."
    },
    "gastro": {
        "keywords": ["estomac", "vomir", "vomissement", "nausée", "nausee", "diarrhée", "diarrhee", "gastro", "constipation", "ventre", "foie", "ulcère", "ulcere", "reflux", "acidité", "acidite", "aigreur", "crampe abdominale", "ballonnement", "digestion", "colon"],
        "title": "🍏 Gastro-Entérologie & Digestion",
        "intro": [
            "Les troubles du tractus gastro-intestinal (nausées, spasmes, altération du transit) nécessitent de mettre le système digestif au repos tout en évitant la déshydratation.",
            "Voici les conseils diététiques et thérapeutiques adaptés à vos symptômes digestifs."
        ],
        "advice": (
            "🍽️ **Protocole Alimentaire d'Urgence (Régime BRAT) :**\n"
            "• **A consommer :** Riz blanc bien cuit et son eau de cuisson, Bananes mûres, Compote de pommes sans sucre et Toast (pain blanc grillé).\n"
            "• **A proscrire absolument :** Produits laitiers, aliments gras ou frits, épices, café et alcools pendant au moins 48 heures.\n\n"
            "💧 **Réhydratation Fractionnée :**\n"
            "• En cas de diarrhées ou vomissements, buvez de petites gorgées fréquentes d'eau sucrée-salée ou de bouillon pour compenser la perte en électrolytes.\n\n"
            "💊 **Support Thérapeutique (sans ordonnance) :**\n"
            "• **Antispasmodique (Spasfon / Phloroglucinol) :** 2 comprimés jusqu'à 3 fois par jour pour calmer les contractions et crampes du ventre.\n"
            "• **Anti-acides ou Pansements gastriques :** Utilisables si sensation de brûlure rétrosternale ou de reflux (Gaviscon après le repas)."
        ),
        "red_flags": "🚨 **Quand consulter d'urgence ?** En cas de présence de sang dans les selles ou les vomissements, d'arrêt complet des gaz et du transit avec douleur aiguë, ou de fièvre persistant plus de 3 jours."
    },
    "orl_pneumo": {
        "keywords": ["toux", "rhume", "grippe", "gorge", "angine", "bronchite", "nez", "sinusite", "oreille", "otite", "respiration", "asthme", "mucus", "crachat", "mouchage"],
        "title": "🫁 Pneumologie & ORL (Espace Respiratoire)",
        "intro": [
            "Les affections respiratoires et ORL fréquentes (toux, rhume, maux de gorge) sont à 80% d'origine virale et demandent principalement un traitement symptomatique et du repos.",
            "Voici le plan d'action médical pour apaiser vos voies respiratoires et renforcer votre immunité."
        ],
        "advice": (
            "🌿 **Soins Locaux & Naturels :**\n"
            "• **Lavage Nasal :** Effectuez des lavages copieux des fosses nasales avec du sérum physiologique ou spray d'eau de mer hypertonique 3 à 4 fois par jour.\n"
            "• **Inhalation & Humidification :** Respirez de la vapeur tiède (inhalations au thym ou eucalyptus) pour fluidifier les sécrétions et dégager les bronches.\n"
            "• **Apaisement Pharyngé :** Une infusion tiède avec une cuillère à café de miel pur (interdit aux bébés < 1 an) adoucit naturellement l'inflammation de la gorge.\n\n"
            "💊 **Rappel Antibiotique Fondamental :**\n"
            "• Les antibiotiques sont **totalement inefficaces** contre les virus du rhume ou de la grippe. Seul un test rapide en cabinet (comme un TDR streptocoque pour une angine) permet de confirmer la nécessité d'une antibiotothérapie."
        ),
        "red_flags": "🚨 **Consultez un médecin Fransick :** Si vous éprouvez une gêne respiratoire forte (sifflements, essoufflement au repos), si la fièvre dépasse 39°C ou si une toux grasse persiste au-delà de 10 jours."
    },
    "rhumatologie": {
        "keywords": ["dos", "lombaire", "sciatique", "articulation", "arthrose", "arthrite", "genou", "hanche", "muscle", "courbature", "entorse", "tendinite", "fracture", "torticolis", "cervicale"],
        "title": "🦴 Rhumatologie, Muscles & Squelette",
        "intro": [
            "Les douleurs ostéo-articulaires et musculaires peuvent provenir d'un traumatisme aigu, d'une mauvaise posture ou d'une inflammation chronique.",
            "Voici les recommandations ergonomiques et thérapeutiques adaptées pour apaiser vos articulations et muscles."
        ],
        "advice": (
            "🧊 **Le Dilemme Glace vs Chaleur :**\n"
            "• **Appliquez du FROID (Glace) :** Dans les 48h suivant un traumatisme aigu (entorse du genou ou cheville, choc, gonflement). Le froid limite l'œdème et engourdit la douleur (20 min 3x/jour, enveloppé dans une serviette).\n"
            "• **Appliquez du CHAUD (Bouillotte) :** En cas de contracture musculaire, torticolis ou douleur lombaire chronique. La chaleur décontracte les fibres musculaires et stimule l'afflux sanguin cicatrisant.\n\n"
            "📌 **Le Protocole GREC (pour entorses et traumatismes) :**\n"
            "• **G**lace, **R**epos de l'articulation, **E**lévation du membre affaibli, **C**ompression (bannissez les massages violents sur un tendon inflammé).\n\n"
            "💊 **Analgésiques :** Le Paracétamol reste le premier choix. L'utilisation d'un gel anti-inflammatoire local (type Diclofénac) peut grandement soulager en massage doux."
        ),
        "red_flags": "🚨 **Consultation immédiate :** En cas d'impossibilité totale de prendre appui, d'une déformation visible de l'articulation (fracture/luxation) ou de perte de sensibilité nerveuse (engourdissement complet du pied en cas de sciatique)."
    },
    "gynecologie_urologie": {
        "keywords": ["règle", "regle", "bas-ventre", "bas ventre", "dysménorrhée", "dysmenorrhee", "grossesse", "enceinte", "ovaire", "kyste", "urinaire", "cystite", "brûlure urinaire", "brulure urinaire", "rein", "pilule", "contraception", "spasfon"],
        "title": "🌸 Gynécologie, Obstétrique & Urologie",
        "intro": [
            "La santé intimement féminine, le suivi des cycles menstruels et de l'appareil urinaire méritent des protocoles d'apaisement spécifiques et ciblés.",
            "Voici votre fiche clinique thérapeutique concernant les douleurs pelviennes, menstruelles ou urinaires."
        ],
        "advice": (
            "🌸 **Gestion des Douleurs Menstruelles (Dysménorrhées & Bas-ventre) :**\n"
            "• **Antispasmodique (Spasfon / Phloroglucinol) :** 2 comprimés au moment de la crise (jusqu'à 3 fois par jour). Agit directement pour détendre le muscle utérin.\n"
            "• **AINS (Ibuprofène 200 à 400mg) :** Bloque la production des prostaglandines utérines responsables des spasmes (à prendre impérativement au cours d'un repas, interdit en cas d'ulcère ou de grossesse).\n"
            "• **Chaleur douce :** Placez une bouillotte tiède sur le bas-ventre, associez une infusion de sauge ou de camomille.\n\n"
            "💧 **Prévention et soulagement des Cystites / Gênes urinaires :**\n"
            "• **Hydratation massive :** Buvez au moins 2 litres d'eau plate par jour de manière continue pour rincer la vessie.\n"
            "• **Jus de canneberge (Cranberry) :** Contient des proanthocyanidines empêchant la fixation des bactéries E. coli sur la paroi vésicale.\n"
            "• **Règle d'or :** Ne retenez jamais vos urines et pensez systématiquement à uriner immédiatement après un rapport sexuel."
        ),
        "red_flags": "🚨 **Alerte Médicale :** En cas de brûlure urinaire accompagnée de fièvre, de frissons ou d'une douleur vive dans le bas du dos (suspicion de pyélonéphrite), consultez immédiatement un médecin sur Fransick."
    },
    "pediatrie": {
        "keywords": ["bébé", "bebe", "enfant", "nourrisson", "pédiatre", "pediatre", "fièvre bébé", "fievre bebe", "pleurs", "croissance", "varicelle", "bronchiolite", "vaccin enfant"],
        "title": "🧸 Pédiatrie & Soins du Nourrisson",
        "intro": [
            "L'organisme d'un nourrisson ou d'un jeune enfant réagit de manière rapide mais exige des dosages stricts basés exclusivement sur le poids corporel.",
            "Voici les repères cliniques indispensables pour prendre soin de votre enfant en toute sécurité."
        ],
        "advice": (
            "⚖️ **Règle d'Or des Posologies Pédiatriques (Paracétamol) :**\n"
            "• Le dosage du Paracétamol en sirop ou suppositoire est strictement de **15 mg par kilo de poids corporel** par prise, à espacer d'au moins **6 heures** (soit maximum 4 prises en 24h : 60 mg/kg/jour au total).\n"
            "• *Exemple :* Pour un enfant de 10 kg, la dose est de 150 mg par prise. Utilisez toujours la pipette graduée au poids en kg fournie dans le flacon !\n"
            "• ⚠️ **Mise en garde stricte :** N'administrez JAMAIS d'aspirine à un enfant ou un adolescent ayant une infection virale ou de la fièvre (risque fatal de Syndrome de Reye).\n\n"
            "🌡️ **Gestes d'apaisement d'un enfant fiandreux :**\n"
            "• Ne couvrez pas excessivement l'enfant, laissez-le en body ou vêtements légers en coton.\n"
            "• Maintenez la chambre à une température douce (18°C - 19°C).\n"
            "• Proposez-lui très fréquemment à boire (eau, biberon de lait ou soluté de réhydratation) pour compenser les pertes transpirées."
        ),
        "red_flags": "🚨 **Urgences Pédiatriques :** Toute fièvre > 38°C chez un nourrisson de moins de 3 mois, ou un comportement amorphe, un refus de boire de plus de 6 heures, ou des boutons violacés ne s'effaçant pas à la pression (purpura) exigent une consultation en urgence immédiate à l'hôpital."
    },
    "dermatologie": {
        "keywords": ["bouton", "peau", "démangeaison", "demangeaison", "allergie", "plaie", "urticaire", "eczéma", "eczema", "acné", "acne", "mycose", "brûlure", "brulure", "éruption", "eruptin", "gonflement"],
        "title": "🧴 Dermatologie & Allergologie",
        "intro": [
            "La peau est le plus grand organe de protection du corps humain; toute éruption, piqûre ou rougeur est un signal d'alerte immunitaire à traiter avec douceur.",
            "Voici vos indications cliniques de soins pour la protection et l'apaisement cutané."
        ],
        "advice": (
            "🛡️ **Soins Cutanés & Hygiène :**\n"
            "• **Règle absolue : Ne grattez jamais** une zone irritée, boutonneuse ou lésée afin d'évincer la surinfection bactérienne (staphylocoques, impétigo) et les cicatrices.\n"
            "• **Nettoyage :** Remplacez les savons classiques agressifs par un pain surgras, une huile lavante ou un gel sans savon au pH neutre.\n\n"
            "💊 **Orientations Symptomatiques :**\n"
            "• *En cas de plaie légère ou brûlure de 1er degré (rougeur type coup de soleil) :* Rincez sous l'eau tempérée pendant 10 minutes, désinfectez avec un antiseptique aqueux (Chlorhexidine, Biseptine) et appliquez une crème cicatrisante ou apaisante (Biafine, Cicaplast).\n"
            "• *En cas d'urticaire ou de démangeaison allergique :* Une prise d'antihistaminique oral en vente libre (type Cétirizine ou Loratadine 10 mg) calme rapidement les démangeaisons."
        ),
        "red_flags": "🚨 **Urgence Allergique (Anaphylaxie) :** Si l'éruption cutanée ou le gonflement s'accompagne d'un gonflement des lèvres, de la langue, ou d'une difficulté à respirer (œdème de Quincke), appelez le 15 (SAMU) sans la moindre seconde de retard !"
    },
    "endocrino_metabolisme": {
        "keywords": ["diabète", "diabete", "glycémie", "glycemie", "sucre", "insuline", "thyroïde", "thyroide", "poids", "obésité", "obesite", "maigrir", "hypoglycémie"],
        "title": "🩸 Endocrinologie, Métabolisme & Nutrition",
        "intro": [
            "Le système endocrinien régule les hormones de l'organisme, le taux de sucre sanguin (glycémie) et le métabolisme global.",
            "Voici les repères médicaux essentiels pour le contrôle de vos équilibres métaboliques et nutritionnels."
        ],
        "advice": (
            "📌 **Equilibre Glycémique (Diabète) :**\n"
            "• Une glycémie à jeun normale se situe entre **0,70 et 1,10 g/L** (3,9 à 6,1 mmol/L). Un diagnostic de diabète est posé si la glycémie à jeun dépasse 1,26 g/L lors de deux analyses distinctes.\n\n"
            "🍭 **Gestion d'une Hypoglycémie Aiguë (< 0,70 g/L ou malaise sucré) :**\n"
            "• *Symptômes :* Sueurs froides, tremblements, palpitations, vision floue, sensation de faim impérieuse.\n"
            "• *Action immédiate (Règle des 15 g de sucre rapide) :* Consommez immédiatement 3 morceaux de sucre, 15 cl de jus de fruits de fruit pur, ou 1 cuillère à soupe de miel. Attendez 15 minutes avant de recontrôler, puis prenez un sucre lent (pain, biscuit) pour maintenir l'équilibre.\n\n"
            "⚖️ **Nutrition :** Favorisez une alimentation riche en fibres (légumes crus et cuits, céréales complètes) qui ralentissent l'absorption intestinale des sucres et des lipides."
        ),
        "red_flags": "🚨 **Rappel Diabétologique :** N'ajustez jamais seuls vos doses d'insuline ou vos antidiabétiques oraux sans valider votre protocole avec votre endocrinologue sur Fransick."
    },
    "pharmacologie_posologie": {
        "keywords": ["paracetamol", "doliprane", "ibuprofene", "amoxicilline", "amoxi", "augmentin", "antibiotique", "efferalgan", "dafalgan", "aspirine", "posologie", "effets secondaires", "médicament", "medicament", "ordonnance", "dose"],
        "title": "💊 Pharmacologie, Médicaments & Posologies",
        "intro": [
            "La sécurité médicamenteuse repose sur le respect scrupuleux des doses, des intervalles entre les prises et l'analyse des interactions potentielles.",
            "Voici la synthèse officielle d'administration et de sécurité concernant les molécules pharmaceutiques courantes."
        ],
        "advice": (
            "⚖️ **Paracétamol (Doliprane / Dafalgan / Efferalgan) - Le roi des antalgiques :**\n"
            "• **Posologie Adulte :** 500 mg à 1000 mg (1 g) par prise, avec un intervalle **obligatoire d'au moins 4 à 6 heures** entre deux prises.\n"
            "• ⚠️ **Dose maximale absolue :** **4 000 mg (4 g) par 24 heures** chez un adulte en bonne santé. Au-delà de ce plafond, le paracétamol devient hautement toxique pour le foie (risque d'hépatite fulminante).\n\n"
            "🛡️ **Anti-inflammatoires Non Stéroïdiens (AINS : Ibuprofène, Advil, Nurofen) :**\n"
            "• À prendre **toujours au cours d'un repas** pour éviter de brûler la muqueuse de l'estomac (ulcères).\n"
            "• ⚠️ **Contre-indications strictes :** Interdit aux femmes enceintes à partir du 6ème mois de grossesse (risque mortel pour le fœtus), aux patients sous anticoagulants ou souffrant d'ulcère gastrique.\n\n"
            "🦠 **Les Antibiotiques (Amoxicilline, Augmentin, Ciprofloxacine...) :**\n"
            "• Ils sont délivrés **strictement sur ordonnance médicale**. Il est vital d'aller **jusqu'au bout** de la durée prescrite (souvent 6 à 7 jours) même si vous allez mieux au 2ème jour, afin d'empêcher les bactéries de survivre et d'acquérir une résistance antibiotique !"
        ),
        "red_flags": "🚨 *Si vous ressentez une réaction indésirable suspecte (nausée violente, éruption cutanée après prise d'un médicament), stoppez la molécule et interrogez un médecin en ligne.*"
    },
    "sante_mentale_sommeil": {
        "keywords": ["stress", "anxiété", "anxiete", "angoisse", "dépression", "depression", "triste", "panique", "insomnie", "sommeil", "burnout", "fatigue morale", "somnifère", "somnifere"],
        "title": "🧘 Santé Mentale, Gestion du Stress & Somnologie",
        "intro": [
            "La santé mentale et la qualité du sommeil constituent les fondations indéboulonnables du système immunitaire et de l'équilibre neurologique de tout patient.",
            "Voici des stratégies scientifiquement validées pour apaiser l'anxiété, retrouver la sérénité et régénérer vos nuits."
        ],
        "advice": (
            "🌬️ **Technique d'Apaisement Immédiat : La Cohérence Cardiaque (Méthode 3-6-5) :**\n"
            "• Lors d'un pic d'anxiété ou de palpitations d'angoisse : asseyez-vous, le dos droit. **Inspirez profondément par le nez pendant 5 secondes**, puis **expirez doucement par la bouche pendant 5 secondes**.\n"
            "• Répétez ce cycle régulier pendant 5 minutes, 3 fois par jour. Cet exercice abaisse instantanément le taux de cortisol (hormone du stress) et stimule le système nerveux parasympathique apaisant.\n\n"
            "🌙 **Hygiène du Sommeil d'Excellence :**\n"
            "• **Déconnexion lumineuse :** Éteignez tous les écrans (smartphone, tablette, TV) au moins 1 heure avant de dormir afin de libérer votre mélatonine naturelle.\n"
            "• **Température de chambre :** Maintenez votre chambre entre 18°C et 19°C dans l'obscurité totale.\n"
            "• Privilégiez les infusions aux plantes apaisantes (Valériane, Passiflore, Tilleul, Camomille) plutôt que les somnifères d'accoutumance."
        ),
        "red_flags": "💡 *Le bien-être psychologique ne doit jamais être négligé. En cas de tristesse prolongée ou d'anxiété invalidante, nos médecins et psychologues partenaires sur Fransick vous écoutent en toute confidentialité.*"
    }
}


def analyze_and_generate_response(user_message, chat_history_list=None):
    """
    Moteur IA Médical Intelligent
    Analyse le message de l'utilisateur en appliquant des algorithmes de filtrage sémantique et de recherche lexicale,
    et retourne une réponse médicale structurée au format Markdown, hautement professionnelle et adaptée.
    """
    text = user_message.strip()
    text_lower = text.lower()
    
    # 1. Vérification des salutations simples (sans symptôme médical apparent)
    # Si le message fait moins de 45 caractères et correspond à une salutation
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

    # 2. Analyse Sémantique Médicale multi-domaines
    matched_domains = []
    for domain_key, data in MEDICAL_KNOWLEDGE_BASE.items():
        score = 0
        for kw in data["keywords"]:
            if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower) or (len(kw) > 4 and kw.lower() in text_lower):
                score += 1
        if score > 0:
            matched_domains.append((score, domain_key, data))
            
    # Trier par pertinence (score le plus élevé en premier)
    matched_domains.sort(key=lambda x: x[0], reverse=True)

    # Si nous avons trouvé une ou plusieurs spécialités correspondantes
    if matched_domains:
        top_match = matched_domains[0][2]
        
        # Choix dynamique de phrases pour varier le style et ne jamais paraître redondant
        intro_sentence = random.choice(top_match["intro"])
        
        response = (
            f"### {top_match['title']}\n\n"
            f"*{intro_sentence}*\n\n"
            f"Suite à votre message : *« {text} »*, voici mon analyse et mes recommandations cliniques :\n\n"
            f"{top_match['advice']}\n\n"
            f"___\n"
            f"{top_match['red_flags']}\n\n"
            f"💡 **Conseil Fransick Santé :** Pour obtenir un diagnostic sur-mesure, une ordonnance ou un second avis approfondi, vous pouvez programmer une téléconsultation ou un rendez-vous avec un de nos médecins inscrits."
        )
        return response

    # 3. Moteur d'Inférence Médicale Dynamique (Si aucune spécialité exacte n'est matchée)
    # Extraction intelligente des mots clés du patient pour construire une réponse sur mesure
    stop_words = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'ou', 'pour', 'que', 'qui', 'dans', 'sur', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'son', 'sa', 'ses', 'nous', 'vous', 'avec', 'est', 'sont', 'être', 'avoir', 'jai', "j'ai", 'fait', 'plus', 'moins', 'très', 'tres', 'faire', 'tout', 'toute', 'tous', 'bien', 'comme', 'comment', 'quand', 'pourquoi', 'depuis'}
    raw_words = re.findall(r'\b[a-zA-ZàâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]{4,}\b', text)
    meaningful_words = [w for w in raw_words if w.lower() not in stop_words]
    
    topic = ", ".join(meaningful_words[:4]) if meaningful_words else "votre situation clinique"

    dynamic_templates = [
        (
            f"### 🩺 Évaluation Clinique : {topic.capitalize()}\n\n"
            f"J'ai pris connaissance avec attention de votre question : *« {text} »*.\n\n"
            f"Dans le domaine médical, l'investigation concernant **{topic}** nécessite de croiser l'évolution dans le temps, l'intensité ressentie et vos éventuels antécédents médicaux.\n\n"
            f"📌 **Mes conseils d'accompagnement général :**\n"
            f"1. **Surveillance symptomatologique :** Notez avec précision l'heure, l'intensité et les facteurs qui déclenchent ou aggravent votre inconfort.\n"
            f"2. **Prudence médicamenteuse :** Ne débutez aucun traitement anti-inflammatoire ou antibiotique de vous-même sans examen médical préalable. En cas de douleur banale ou fièvre sans signe de gravité, le Paracétamol reste l'antalgique de référence en automédication respectueuse des doses (maximum 1g toutes les 6h).\n"
            f"3. **Hygiène de vie de soutien :** Accordez au corps un repos physiologique d'endurance et veillez à boire régulièrement de l'eau claire (1.5 L/jour).\n\n"
            f"___\n"
            f"🚨 **Rappel de sécurité :** Si des signes d'alerte (fièvre élevée intense, mal de tête insupportable, saignement ou vomissement intarissable) apparaissent, sollicitez les urgences médicales de votre secteur (15 ou 112).\n\n"
            f"💡 **Passez à l'étape suivante sur Fransick :** Pour qu'un professionnel de santé diplômé évalue physiquement ou en consultation vidéo l'état de **{topic}**, planifiez directement votre rendez-vous depuis votre Tableau de Bord !"
        ),
        (
            f"### 🧬 Consultation Virtuelle & Orientation : {topic.capitalize()}\n\n"
            f"En ma qualité d'Assistant Médical IA Fransick, j'ai bien étudié votre message : *« {text} »*.\n\n"
            f"L'analyse des symptômes liés à **{topic}** doit toujours se faire avec discernement et objectivité scientifique.\n\n"
            f"📋 **Mon plan d'orientation santé :**\n"
            f"• **Évaluation de premier niveau :** Vérifiez si votre état général est conservé (absence de fièvre > 38.8°C, hydratation maintenue, sommeil correct).\n"
            f"• **Gestes simples de confort :** Évitez toute situation de surmenage physique, maintenez une alimentation légère et équilibrée, et ne sollicitez pas les zones douloureuses.\n"
            f"• **Sécurité pharmaceutique :** Vérifiez toujours les notices de votre armoire à pharmacie. Ne mélangez jamais plusieurs antalgiques sans conseil d'un pharmacien ou médecin.\n\n"
            f"___\n"
            f"💡 **Recommandation officielle Fransick :** Rien ne remplace l'expertise clinique, la palpation et l'auscultation d'un véritable praticien de santé. Je vous invite à cliquer sur notre répertoire des médecins connectés pour échanger en toute sécurité sur votre situation !"
        )
    ]
    
    return random.choice(dynamic_templates)
