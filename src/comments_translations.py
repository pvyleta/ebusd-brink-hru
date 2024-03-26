

COMMENT_HEADER = '''## This ebus config may work for Ubbink, VisionAIR, WOLF CWL series, Viessmann and some other systems that are just re-branded Brink devices
## sources:
## - Original idea and some dividers: https://github.com/dstrigl/ebusd-config-brink-renovent-excellent-300
## - Brink Service Tool (decompiled via Jetbrains DotPeak): https://www.brinkclimatesystems.nl/tools/software-brink-service-tool-en
## - Renovent 150 Datasheet: https://manuals.plus/brink/renovent-sky-150-plus-mechanical-ventilation-with-heat-recovery-manual
## - Modbus Module Datasheet: https://www.brinkclimatesystems.nl/documenten/modbus-uwa2-b-uwa2-e-installation-regulations-614882.pdf
## Message names are based on official Brink Service Tool translations with removed spaces and special characters. 
## Message comment is the name of the parameter as used internally in code (as to help if the translation itself is confusing)
## 
## For ebusd configuration files for the complete Brink portfolio go to https://github.com/pvyleta/ebusd-brink-hru
'''
COMMENT_COMMON_COMMANDS = '''
## COMMON HRU COMMANDS ## (WTWCommands.cs - Some of them might not be applicable for this device, use with caution)
'''
COMMENT_CURRENT_STATE = '''
## Curent state and sensors ##
'''
COMMENT_PARAMETERS = '''
## Configuration parameters ## (values in brackets next to field are definitions of those fields values from Brink Service Tool.)
'''
COMMENT_SLAVE_AND_CIRCUIT = '''
## Slave address and Circuit ##
## Fill in the slave address of your device (hexa without \'0x\' prefix) instead of [fill_your_slave_address_here]
## Then just rename this file to [fill_your_slave_address_here].csv and you should be good to use it in ebusd.
'''
# The following translations were done through ChatGPT, so they might not be super correct - although hey, better than nothing for zero effort.

translations = {
    "en": {
        "COMMENT_HEADER": COMMENT_HEADER,
        "COMMENT_COMMON_COMMANDS": COMMENT_COMMON_COMMANDS,
        "COMMENT_CURRENT_STATE": COMMENT_CURRENT_STATE,
        "COMMENT_PARAMETERS": COMMENT_PARAMETERS,
        "COMMENT_SLAVE_AND_CIRCUIT": COMMENT_SLAVE_AND_CIRCUIT,
    },
    "de": {
        "COMMENT_HEADER": '''## Diese Ebus-Konfiguration könnte für Ubbink, VisionAIR, WOLF CWL Serien, Viessmann und einige andere Systeme funktionieren, die nur umgebrandete Brink-Geräte sind
## Quellen:
## - Ursprüngliche Idee und einige Trennzeichen: https://github.com/dstrigl/ebusd-config-brink-renovent-excellent-300
## - Brink Service Tool (decompiliert via Jetbrains DotPeak): https://www.brinkclimatesystems.nl/tools/software-brink-service-tool-en
## - Renovent 150 Datenblatt: https://manuals.plus/brink/renovent-sky-150-plus-mechanical-ventilation-with-heat-recovery-manual
## - Modbus Modul Datenblatt: https://www.brinkclimatesystems.nl/documenten/modbus-uwa2-b-uwa2-e-installation-regulations-614882.pdf
## Nachrichtennamen basieren auf den offiziellen Übersetzungen des Brink Service Tools mit entfernten Leerzeichen und Sonderzeichen.
## Nachrichtenkommentar ist der Name des Parameters, wie er intern im Code verwendet wird (um zu helfen, wenn die Übersetzung selbst verwirrend ist)
''',
        "COMMENT_COMMON_COMMANDS": '''
## ALLGEMEINE HRU BEFEHLE ## (WTWCommands.cs - Einige davon sind möglicherweise nicht für dieses Gerät anwendbar, mit Vorsicht verwenden)
''',
        "COMMENT_CURRENT_STATE": '''
## Aktueller Zustand und Sensoren ##
''',
        "COMMENT_PARAMETERS": '''
## Konfigurationsparameter ## (Werte in Klammern neben dem Feld sind Definitionen dieser Feldwerte aus dem Brink Service Tool.)
''',
        "COMMENT_SLAVE_AND_CIRCUIT": '''
## Slave-Adresse und Schaltung ##
## Geben Sie die Slave-Adresse Ihres Geräts ein (Hexa ohne \'0x\' Präfix) anstelle von [fill_your_slave_address_here]
## Benennen Sie dann diese Datei einfach um in [fill_your_slave_address_here].csv und Sie sollten sie in ebusd verwenden können.
''',
    },
    "fr": {
        "COMMENT_HEADER": '''## Cette configuration ebus peut fonctionner pour Ubbink, VisionAIR, les séries WOLF CWL, Viessmann et certains autres systèmes qui sont juste des dispositifs Brink re-marqués
## sources :
## - Idée originale et certains séparateurs : https://github.com/dstrigl/ebusd-config-brink-renovent-excellent-300
## - Outil de service Brink (décompilé via Jetbrains DotPeak) : https://www.brinkclimatesystems.nl/tools/software-brink-service-tool-en
## - Fiche technique Renovent 150 : https://manuals.plus/brink/renovent-sky-150-plus-mechanical-ventilation-with-heat-recovery-manual
## - Fiche technique du module Modbus : https://www.brinkclimatesystems.nl/documenten/modbus-uwa2-b-uwa2-e-installation-regulations-614882.pdf
## Les noms des messages sont basés sur les traductions officielles de l'outil de service Brink avec espaces et caractères spéciaux supprimés.
## Le commentaire du message est le nom du paramètre tel qu'utilisé en interne dans le code (pour aider si la traduction elle-même est déroutante)
''',
        "COMMENT_COMMON_COMMANDS": '''
## COMMANDES HRU COMMUNES ## (WTWCommands.cs - Certaines d'entre elles peuvent ne pas être applicables pour cet appareil, à utiliser avec prudence)
''',
        "COMMENT_CURRENT_STATE": '''
## État actuel et capteurs ##
''',
        "COMMENT_PARAMETERS": '''
## Paramètres de configuration ## (les valeurs entre parenthèses à côté du champ sont des définitions de ces valeurs de champ du Brink Service Tool.)
''',
        "COMMENT_SLAVE_AND_CIRCUIT": '''
## Adresse esclave et circuit ##
## Remplissez l'adresse esclave de votre appareil (hexa sans préfixe '0x') au lieu de [fill_your_slave_address_here]
## Renommez ensuite simplement ce fichier en [fill_your_slave_address_here].csv et vous devriez pouvoir l'utiliser dans ebusd.
''',
    },
    "it": {
        "COMMENT_HEADER": '''## Questa configurazione ebus potrebbe funzionare per Ubbink, VisionAIR, serie WOLF CWL, Viessmann e alcuni altri sistemi che sono semplicemente dispositivi Brink con marchio diverso
## fonti:
## - Idea originale e alcuni divisori: https://github.com/dstrigl/ebusd-config-brink-renovent-excellent-300
## - Strumento di servizio Brink (decompilato tramite Jetbrains DotPeak): https://www.brinkclimatesystems.nl/tools/software-brink-service-tool-en
## - Scheda tecnica Renovent 150: https://manuals.plus/brink/renovent-sky-150-plus-mechanical-ventilation-with-heat-recovery-manual
## - Scheda tecnica modulo Modbus: https://www.brinkclimatesystems.nl/documenten/modbus-uwa2-b-uwa2-e-installation-regulations-614882.pdf
## I nomi dei messaggi si basano sulle traduzioni ufficiali dello Strumento di servizio Brink con spazi e caratteri speciali rimossi.
## Il commento al messaggio è il nome del parametro come utilizzato internamente nel codice (per aiutare se la traduzione di per sé è confusa)
''',
        "COMMENT_COMMON_COMMANDS": '''
## COMANDI HRU COMUNI ## (WTWCommands.cs - Alcuni di essi potrebbero non essere applicabili per questo dispositivo, usare con cautela)
''',
        "COMMENT_CURRENT_STATE": '''
## Stato corrente e sensori ##
''',
        "COMMENT_PARAMETERS": '''
## Parametri di configurazione ## (i valori tra parentesi accanto al campo sono definizioni di quei valori dei campi dallo Strumento di servizio Brink.)
''',
        "COMMENT_SLAVE_AND_CIRCUIT": '''
## Indirizzo slave e circuito ##
## Inserire l'indirizzo slave del proprio dispositivo (hexa senza prefisso '0x') al posto di [fill_your_slave_address_here]
## Rinominare poi semplicemente questo file in [fill_your_slave_address_here].csv e si dovrebbe essere in grado di utilizzarlo in ebusd.
''',
    },
    "es": {
        "COMMENT_HEADER": '''## Esta configuración de ebus puede funcionar para Ubbink, VisionAIR, series WOLF CWL, Viessmann y algunos otros sistemas que son simplemente dispositivos Brink re-marcados
## fuentes:
## - Idea original y algunos divisores: https://github.com/dstrigl/ebusd-config-brink-renovent-excellent-300
## - Herramienta de Servicio Brink (decompilada vía Jetbrains DotPeak): https://www.brinkclimatesystems.nl/tools/software-brink-service-tool-en
## - Hoja de datos Renovent 150: https://manuals.plus/brink/renovent-sky-150-plus-mechanical-ventilation-with-heat-recovery-manual
## - Hoja de datos del Módulo Modbus: https://www.brinkclimatesystems.nl/documenten/modbus-uwa2-b-uwa2-e-installation-regulations-614882.pdf
## Los nombres de los mensajes se basan en las traducciones oficiales de la Herramienta de Servicio Brink con espacios y caracteres especiales eliminados.
## El comentario del mensaje es el nombre del parámetro tal como se usa internamente en el código (para ayudar si la traducción en sí es confusa)
''',
        "COMMENT_COMMON_COMMANDS": '''
## COMANDOS HRU COMUNES ## (WTWCommands.cs - Algunos de ellos pueden no ser aplicables para este dispositivo, usar con precaución)
''',
        "COMMENT_CURRENT_STATE": '''
## Estado actual y sensores ##
''',
        "COMMENT_PARAMETERS": '''
## Parámetros de configuración ## (los valores entre paréntesis junto al campo son definiciones de esos valores de campo del Herramienta de Servicio Brink.)
''',
        "COMMENT_SLAVE_AND_CIRCUIT": '''
## Dirección esclava y circuito ##
## Complete la dirección esclava de su dispositivo (hex sin prefijo '0x') en lugar de [fill_your_slave_address_here]
## Luego simplemente renombre este archivo a [fill_your_slave_address_here].csv y debería poder usarlo en ebusd.
''',
    },
    "pl": {
        "COMMENT_HEADER": '''## Ta konfiguracja ebus może działać dla Ubbink, VisionAIR, serii WOLF CWL, Viessmann oraz niektórych innych systemów, które są po prostu przemarkowane urządzeniami Brink
## źródła:
## - Oryginalny pomysł i niektóre dzielniki: https://github.com/dstrigl/ebusd-config-brink-renovent-excellent-300
## - Narzędzie serwisowe Brink (zdekompilowane przez Jetbrains DotPeak): https://www.brinkclimatesystems.nl/tools/software-brink-service-tool-en
## - Karta katalogowa Renovent 150: https://manuals.plus/brink/renovent-sky-150-plus-mechanical-ventilation-with-heat-recovery-manual
## - Karta katalogowa modułu Modbus: https://www.brinkclimatesystems.nl/documenten/modbus-uwa2-b-uwa2-e-installation-regulations-614882.pdf
## Nazwy wiadomości bazują na oficjalnych tłumaczeniach Narzędzia serwisowego Brink z usuniętymi spacjami i znakami specjalnymi.
## Komentarz wiadomości to nazwa parametru używana wewnętrznie w kodzie (aby pomóc, jeśli samo tłumaczenie jest mylące)
## 
## Aby uzyskać pliki konfiguracyjne ebusd dla całego portfolio Brink, przejdź do https://github.com/pvyleta/ebusd-brink-hru
''',
        "COMMENT_COMMON_COMMANDS": '''
## WSPÓLNE KOMENDY HRU ## (WTWCommands.cs - Niektóre z nich mogą nie być odpowiednie dla tego urządzenia, używaj z ostrożnością)
''',
        "COMMENT_CURRENT_STATE": '''
## Aktualny stan i czujniki ##
''',
        "COMMENT_PARAMETERS": '''
## Parametry konfiguracyjne ## (wartości w nawiasach obok pola to definicje tych wartości pól z Narzędzia serwisowego Brink.)
''',
        "COMMENT_SLAVE_AND_CIRCUIT": '''
## Adres slave i obwód ##
## Wpisz adres slave swojego urządzenia (hexa bez prefixu \'0x\') zamiast [fill_your_slave_address_here]
## Następnie po prostu zmień nazwę tego pliku na [fill_your_slave_address_here].csv i powinieneś móc go używać w ebusd.
''',
    },
    "nl": {
        "COMMENT_HEADER": '''## Deze ebus-configuratie kan werken voor Ubbink, VisionAIR, WOLF CWL-serie, Viessmann en sommige andere systemen die gewoon opnieuw gelabelde Brink-apparaten zijn
## bronnen:
## - Origineel idee en enkele scheiders: https://github.com/dstrigl/ebusd-config-brink-renovent-excellent-300
## - Brink Service Tool (gedecompileerd via Jetbrains DotPeak): https://www.brinkclimatesystems.nl/tools/software-brink-service-tool-en
## - Renovent 150 Datasheet: https://manuals.plus/brink/renovent-sky-150-plus-mechanical-ventilation-with-heat-recovery-manual
## - Modbus Module Datasheet: https://www.brinkclimatesystems.nl/documenten/modbus-uwa2-b-uwa2-e-installation-regulations-614882.pdf
## Berichtnamen zijn gebaseerd op officiële Brink Service Tool vertalingen met verwijderde spaties en speciale tekens.
## Berichtcommentaar is de naam van de parameter zoals intern in de code gebruikt (om te helpen als de vertaling zelf verwarrend is)
## 
## Voor ebusd-configuratiebestanden voor het complete Brink-portfolio ga naar https://github.com/pvyleta/ebusd-brink-hru
''',
        "COMMENT_COMMON_COMMANDS": '''
## GEMEENSCHAPPELIJKE HRU COMMANDO'S ## (WTWCommands.cs - Sommige zijn mogelijk niet van toepassing op dit apparaat, gebruik met voorzichtigheid)
''',
        "COMMENT_CURRENT_STATE": '''
## Huidige staat en sensoren ##
''',
        "COMMENT_PARAMETERS": '''
## Configuratieparameters ## (waarden tussen haakjes naast veld zijn definities van die veldwaarden uit Brink Service Tool.)
''',
        "COMMENT_SLAVE_AND_CIRCUIT": '''
## Slave-adres en Circuit ##
## Vul het slave-adres van uw apparaat in (hexa zonder '0x' voorvoegsel) in plaats van [fill_your_slave_address_here]
## Hernoem dit bestand vervolgens naar [fill_your_slave_address_here].csv en u zou het in ebusd moeten kunnen gebruiken.
''',
    },
}

