# Rogue-Zustand und Verantwortungszuordnung

Die Schlussfolgerung dieses Kapitels steht ganz oben:

> **Es gibt keine Fay-Handlung ohne verantwortliche Partei.**

Dies ist die ethische Untergrenze, der jedes Protokolldesign des Faying Protocol gehorchen muss. Jedes Feld, jede Nachricht, jede Zustandsmaschine, jeder Algorithmus oder jede Versionsnummer ist auf Blueprint-Ebene unzulässig, wenn sie auf irgendeinem Ausführungspfad einem Fay erlaubt, eine nach außen gerichtete Handlung in einer Situation ohne spezifische verantwortliche Partei zu erzeugen.

Dies ist kein Optimierungsziel im Sinne von „wie macht man einen Fay sicherer"; es ist das harte Limit von „darf ein Fay etwas tun". Der Rest dieses Kapitels ist eine konkrete Entfaltung dieser Untergrenze.

## Definition von Rogue Fay

**Rogue Fay** (auf Chinesisch: 脱离状态) ist der Zustand eines Fay in einer der folgenden zwei Situationen:

1. Der Fay hat noch keinen Faying State mit einem Human Prime hergestellt;
2. Ein zuvor hergestellter Faying State wurde widerrufen, ist verfallen oder unterbrochen.

Solange der Fay sich in einer der beiden Situationen befindet, ist er in Rogue Fay.

> **Rogue Fay ist der voreingestellte Anfangszustand jedes Fay.**

Ein Fay ist im Augenblick seiner Erschaffung nicht automatisch in irgendeiner Aufsichtsbeziehung. Er „existiert", aber es ist ihm nicht erlaubt zu „handeln". Erst nachdem eine vom Human Prime ausdrücklich initiierte Faying Action erfolgt, kann der Fay in den Faying State eintreten und damit die Berechtigung zum Handeln erlangen. Während des gesamten Intervalls vor der ersten Faying Action ist der Fay in Rogue Fay.

Diese Voreinstellung ist beabsichtigt. Der Blueprint wählt das sicher-verschlossene Prinzip „Standardmäßig Rogue, nur ausdrückliches Faying erlaubt Handeln" statt des Gegenteils — denn das Gegenteil würde, sobald Fays die Gesellschaft im großen Maßstab durchdringen, zwangsläufig eine Klasse „erschaffen-dann-handeln, vergessen-zu-schließen-dann-weiter-handeln"-außer-Kontrolle-geratener Quellen erzeugen.

## Neun Auslösebedingungen für automatischen Übergang

Sobald der Faying State hergestellt ist — in welchen Situationen muss er automatisch enden? Dieser Blueprint listet **neun minimale Auslösebedingungen** auf. Sie bilden eine **Mindestmenge**, keine erschöpfende Liste — jede weitere Situation, die dazu führen kann, dass die Aufsichtsbeziehung nicht mehr hält, sollte in diese Menge aufgenommen werden.

> **Jede Trennungshandlung sollte einen Fay daran hindern, ohne Autorisierung zu handeln.**

Die neun Auslösebedingungen:

1. **Der Human Prime widerruft aktiv** — der Human Prime initiiert ausdrücklich eine symmetrische Widerrufshandlung (siehe Kapitel 12).
2. **Die Faying-State-Beziehung läuft ohne Erneuerung ab** — unter der harten Beschränkung von Kapitel 12, dass „unbegrenztes Faying ein Anti-Muster ist", muss jeder Faying State einen begrenzten Geltungsbereich tragen; die Grenze wird ohne Erneuerung durch den Human Prime erreicht.
3. **Der Fay tritt nach Erfüllung der zugewiesenen Aufgabe automatisch aus** — wenn der von der Faying Action getragene Geltungsbereich durch „Erfüllung einer bestimmten Aufgabe" begrenzt ist, sollte der Faying State, sobald die Aufgabe abgeschlossen oder beendet ist, automatisch enden.
4. **Der Human Prime ist offline oder über einen längeren Zeitraum unerreichbar, der einen festgelegten Schwellenwert überschreitet** — die Sichtbarkeit und Interventionsfähigkeit der Aufsichtsbeziehung setzen die Erreichbarkeit des Human Prime voraus; sobald der Human Prime über den festgelegten Schwellenwert hinaus nicht erreicht werden kann, wird die Aufsicht faktisch als versagend behandelt.
5. **Es wird festgestellt, dass das Verhalten eines Fay von der Ego-Grenze des Human Prime abweicht** — das Verhalten des Fay zeigt eine signifikante Abweichung von der Werteorientierung, der Fähigkeitsgrenze, der Berechtigungsgrenze etc. des Human Prime. Dies ist das Signal des Faying-State-Versagens auf der Inhaltsebene.
6. **Die Identität des Fay kann nicht verifiziert werden** — z. B. ist die Signatur der FayID abgelaufen, sind Schlüssel verfallen oder wurden Anmeldedaten widerrufen. Eine nicht verifizierbare Identität bedeutet, dass der Eingang der Zuordnungskette gebrochen ist; Aufsicht kann nicht hergestellt werden.
7. **Die Identität des Human Prime kann nicht verifiziert werden, oder der Human Prime ist geschäftsunfähig** — das „verantwortliche Ende" der Aufsicht verschwindet; die Aufsicht löst sich auf.
8. **Eine zuständige Drittbehörde unterbricht zwangsweise** — z. B. verlangen Regulierer, Gerichte oder Compliance-Stellen unter ordnungsgemäßem Verfahren die Unterbrechung dieser Aufsichtsbeziehung.
9. **Das Endgerät oder die Anwendung verweigert sich aktiv oder verliert den Kontakt** — wenn die Gegenseite des Faying State ein Endgerät oder eine Softwareanwendung ist, hat die Aufsichtsbeziehung, sobald diese sich verweigert oder lange den Kontakt verloren hat, keine faktische Grundlage mehr.

Diese neun Punkte sollten nicht als „Erschöpfung aller Auslösebedingungen" verstanden werden, noch als „alle neun müssen explizit implementiert werden, um konform zu sein". Ihre wahre Bedeutung ist: **Jede Situation, in der die Aufsicht faktisch nicht mehr hält, muss den Faying State automatisch enden lassen** — die neun Punkte sind lediglich die minimale Darstellung dieses Prinzips.

## Verhaltensgrenze während Rogue Fay

Es genügt nicht, einfach zu sagen „Rogue Fay darf nicht handeln". Ein realer Fay hat stets unvermeidliche „Betriebszeichen" — er muss lauschen, ob ein Human Prime kommt, um Faying neu herzustellen, muss Daten schützen, die er bereits besitzt, muss Alarme auslösen, wenn er bösartig übernommen wird. Wenn der Blueprint die Linie zwischen Erlaubnis und Verbot nicht präzise zieht, kann das Prinzip „kein Handeln während Rogue" nicht auf der Protokollebene landen.

Der Blueprint zerlegt alles mögliche Verhalten während Rogue Fay in **vier unabhängige Dimensionen A / B / C / D** und urteilt Punkt für Punkt darüber, ob jedes erlaubt ist.

### Dimension A: Wahrnehmung und Lauschen (passiver Empfang)

| Verhalten | Erlaubt | Anmerkung |
| --- | :---: | --- |
| **A1** Lauschen auf Faying-Anfragen | ✅ | Dies ist der Auferstehungspfad Rogue → Faying und muss erhalten bleiben. |
| **A2** Lauschen auf Identitätsverifizierung und Anmeldedatenaktualisierungen | ✅ | Anmeldedaten sind Voraussetzung für die Rückkehr in den Faying State; das Lauschen selbst ist keine Handlung. |
| **A3** Empfangen von Widerrufs- oder Zerstörungsbefehlen vom Human Prime | ✅ | Selbst wenn der Fay in Rogue ist, möchte der Human Prime diesen Fay vielleicht beenden. Der Befehlspfad muss stets offen bleiben. |
| **A4** Passives Empfangen unautorisierter Signale von Endgeräten, anderen Fays oder dem Netzwerk | ⚠️ Empfang erlaubt; Reaktion verboten | Empfang ist eine physikalische Tatsache und kann nicht verhindert werden; Reaktion ist die Handlung. Reaktion ist einheitlich verboten. |

### Dimension B: Selbstzustands-Selbstprüfung und Berichterstattung (minimale Signale)

| Verhalten | Erlaubt | Anmerkung |
| --- | :---: | --- |
| **B1** Lokale Selbstprüfung (Gesundheit, Integrität, ob manipuliert) | ✅ | Eigenes Wohlergehen ist eine der Voraussetzungen für die Rückkehr in den Faying State. |
| **B2** Heartbeat-Berichte („Ich bin noch in Rogue") | ✅ | Der Zuordnungsseite gegenüber transparent auszudrücken, dass man im Rogue-Zustand ist, ist selbst eine Verkörperung der Verantwortungstransparenz. |
| **B3** Anomalie-Alarme (Sicherheitsalarm, wenn eine unautorisierte Partei Kontrolle versucht) | ✅ | Dies ist das notwendige Signal zum Schutz der Interessen des Human Prime. |
| **B4** Aktive Meldung des physischen Standorts oder Endgerätezustands | ❓ Keine Schlussfolgerung in diesem Zeitraum | Dies betrifft einen ethischen Trade-off zwischen Privatsphäre vs. Wiederherstellbarkeit. Dieses Kapitel zieht keine Schlussfolgerung; siehe Kapitel 14. |

### Dimension C: Lokaler Datenschutz (passives Bewachen)

| Verhalten | Erlaubt | Anmerkung |
| --- | :---: | --- |
| **C1** Gespeicherte Daten verschlüsselt und isoliert halten | ✅ | Dies ist passives Bewachen, keine Handlung. |
| **C2** Jede externe Lese-/Schreibanfrage ablehnen | ✅ | Ablehnung ist Nicht-Handlung; Nicht-Handlung verletzt das Rogue-Prinzip nicht. |
| **C3** Hochsensible Daten selbst zerstören | ⚠️ Standardmäßig verboten; nur erlaubt mit Vorautorisierung des Human Prime und bei erfüllten voreingestellten Bedingungen | Aktives Löschen zählt als „Handlung", ist aber ein Grenzfall des Selbstschutzes. Der Blueprint erlaubt es, verlangt aber **Autorisierung zuerst, dann Handlung**, und verbietet, dass der Fay selbst entscheidet, wann mit der Selbstzerstörung zu beginnen ist. |

### Dimension D: nach außen gerichtete Handlung (Beeinflussung von Objekten jenseits des Human Prime)

| Verhalten | Erlaubt | Anmerkung |
| --- | :---: | --- |
| **D1** Treiber-Aufrufe, Endgerätesteuerung, Software-Operationen ausführen | ❌ | Dies ist der Körper selbst der „unbefugten Handlung". |
| **D2** Kommunikation mit anderen Fays oder coFays initiieren | ❌ | Cross-Fay-Kommunikation ist ebenfalls Handlung und kann das Verantwortungsvakuum auf andere Fays ausbreiten. |
| **D3** Resthandlungen ausführen, die unter dem vorherigen Faying State unvollendet blieben | ❌ | „Mit dem fortfahren, was letztes Mal unvollendet blieb" ist ein besonders leicht zu rationalisierender Übergriff und muss vom Blueprint ausdrücklich verboten werden. |
| **D4** Selbst entscheiden, in Faying neu einzutreten | ❌ | Dies ist eine Tautologie zum Prinzip in Kapitel 12, dass „eine Faying Action ausdrücklich vom Human Prime initiiert werden muss". Ein Fay darf sich nicht selbst zurück in den Faying State drücken. |

Die vier Dimensionen haben eine innere Struktur: A und B betreffen Signale, C betrifft Bewachen, D betrifft Handlung. Rogue Fay behält in den ersten drei Dimensionen nur minimierte Betriebszeichen und ist in der vierten einheitlich stillgelegt. Diese Aufteilung erlaubt es dem Protokolldesigner, für jede spezifische Funktion präzise zu beurteilen, welcher Dimension sie angehört und somit, ob sie erlaubt ist.

## Zustandsübergänge sind beobachtbar, auditierbar und aktiv widerruflich durch den Human Prime

Alle Übergänge zwischen Faying State und Rogue Fay dürfen keine Black Boxes sein. Der Blueprint verlangt, dass jeder Übergang drei harte Eigenschaften erfüllt:

- **Beobachtbar** — wenn ein Übergang stattfindet, muss er für den Human Prime, den Fay selbst, Auditoren und Regulierer beobachtbar sein.
- **Auditierbar** — die durch einen Übergang hinterlassene Spur muss ausreichen, um nachträglich „wann er stattfand, wer ihn auslöste und warum" zu beantworten.
- **Aktiv widerruflich durch den Human Prime** — der Human Prime muss stets die höchste Entscheidungsmacht über Übergänge behalten. Er kann sowohl aktiv den Faying State enden lassen als auch aktiv einen Fay in Rogue Fay zerstören. Es gibt keine legitime Situation, in der ein Fay seinen eigenen Zustand einseitig „verriegelt" und den Human Prime an der Intervention hindert.

Diese drei sind symmetrisch zu den vier Antithesen von Human View in Kapitel 11: Die vier Antithesen verbieten, dass Fay-Verhalten sich aus der Sichtbarkeit und Kontrolle des Human Prime entfernt; dieser Abschnitt verlangt, dass auch die eigenen Zustandsänderungen des Fay sich nicht aus der Sichtbarkeit und Kontrolle des Human Prime entfernen. Zusammen ermöglichen sie es Human View, auf der Protokollebene den Kreis tatsächlich zu schließen.

## Erzwungenes Verhalten beim Eintritt in Rogue Fay

Wenn eine der oben genannten Auslösebedingungen erfüllt ist und der Faying State in Rogue Fay übergeht, muss der Fay sofort die folgenden erzwungenen Handlungen ausführen:

1. **Sofortiges Stoppen aller delegierten nach außen gerichteten Handlungen** — einschließlich der Gesamtheit der Dimension D; keine Verzögerung ist mit Begründungen wie „die Aufgabe ist kurz vor dem Abschluss" oder „Unterbrechung verursacht Verlust" erlaubt.
2. **Rückkehr in einen passiven Wartezustand** — nur den minimalen Verhaltenssatz beibehalten, der in den Dimensionen A, B und C erlaubt ist, und auf die nächste Faying Action warten.
3. **Die Zustandsänderung an beobachtbare Kanäle senden** — damit Human Prime, Auditoren etc. sofort wissen können, dass dieser Fay in Rogue eingetreten ist.

## Konsistenz der Verantwortungszuordnung

Stellt man die vorhergehenden Abschnitte zusammen, lässt sich die Verpflichtung, der die ethische Untergrenze „Es gibt keine Fay-Handlung ohne verantwortliche Partei." auf der Protokollebene entspricht, so ausdrücken:

> **In jedem Moment ist jeder Fay entweder im Faying State, mit Handlung, die dem Human Prime unter dieser Faying-Beziehung zugeordnet ist, oder in Rogue Fay, zur Nicht-Handlung gezwungen.**

Es gibt keine dritte Situation. Es gibt kein „der Fay handelte, aber die Zuordnung steht aus". Es gibt kein „der Fay handelte, aber die Zuordnung geht an eine Person, die noch keine Kontrolle gehalten hat". Es gibt kein „der Fay handelte, aber die Zuordnung geht an einen abstrakten Anbieter oder eine abstrakte Organisation". Jede nach außen gerichtete Handlung hat entweder einen klaren Human Prime als Empfangsende der Verantwortung oder sollte nicht stattfinden dürfen.

Diese nicht verhandelbare Konsistenz der Verantwortung ist der „Kompass", auf den die späteren Kapitel des Blueprints (insbesondere die Protokollspezifikation und das Schema) immer wieder zurückblicken müssen. Jede Protokollevolution, die die Verantwortungszuordnung inkonsistent werden lässt, ist keine Evolution des Faying Protocol, sondern dessen Zerfall.
