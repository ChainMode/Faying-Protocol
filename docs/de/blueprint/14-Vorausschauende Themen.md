# Vorausschauende Themen

> **Die folgenden Themen liegen außerhalb des Geltungsbereichs des aktuellen Faying-Protokoll-Designs.**

Dies ist das letzte Kapitel des Blueprints und das einzige Kapitel, dessen Stil sich von allen anderen unterscheidet. Es zieht keine Schlussfolgerungen; es zählt aufrichtig die offenen Fragen auf. Das hat zwei Zwecke: dem Leser nach dem Lesen des Blueprints genau zu sagen, was das aktuelle Faying Protocol löst und was nicht; und klare Plug-in-Punkte für spätere separate Spezifikationen zu lassen.

Jedes Thema in diesem Kapitel bleibt in diesem Zeitraum **ohne Schlussfolgerung**. Wenn eine einfach aussehende Frage nicht beantwortet wurde, ist das kein Versäumnis; es ist Zurückhaltung.

## Andere Arten von Faying-Beziehungen

Das Faying Protocol dieses Zeitraums deckt nur eine Beziehungsart ab: **Human Prime ↔ iFay**. Darüber hinaus sind mindestens die folgenden vier Beziehungsarten noch nicht in das Protokolldesign aufgenommen.

**Eine direkte Faying-Beziehung zwischen Mensch und Endgerät** — der Blueprint dieses Zeitraums wählt iFay als die einzige Entitätsform, der vertraut wird, den Aufsichtsvertrag zu tragen; daher muss das „Sich-im-kontrollierten-Zustand-Befinden" des Endgeräts abgeleitet durch den Faying State des iFay ausgedrückt werden. Ob in einer zukünftigen Phase „ein Human Prime eine Faying-Beziehung direkt mit einem Endgerät herstellt" eingeführt werden soll, erfordert zunächst die Beantwortung mehrerer tiefer Fragen: Hat das Endgerät genug „Identitätsintegrität", um einen Aufsichtsvertrag zu tragen? Wird eine direkte Beziehung dadurch, dass sie auf der Protokollebene iFay umgeht, die Verantwortungskette schwerer rückverfolgbar machen und die Sichtbarkeit von Human View stattdessen verschlechtern? Wenn die beiden Pfade „direkt" und „abgeleitet durch iFay" koexistieren, wie ist die Eindeutigkeit der Zuordnung zu garantieren? Diese Fragen haben in diesem Zeitraum keine zufriedenstellende Antwort.

**Eine direkte Faying-Beziehung zwischen Mensch und Softwareanwendung** — homolog zum vorherigen Punkt, aber mit einer weiteren Komplexitätsschicht. Eine Softwareanwendung selbst ist oft modular, prozess- und netzwerkübergreifend. Beim direkten Aufbau einer Faying-Beziehung mit einer Anwendung muss zunächst die Grenze „der Anwendung" selbst präzise definiert werden, und diese Definition ist über verschiedene Ökosysteme und Bereitstellungsformen hinweg noch nicht konvergiert. Der Grund, warum dieser Zeitraum die Erweiterung von Phase 3 zu „die Softwareanwendung abgeleitet durch den iFay übernehmen" gemacht hat, ist gerade, dieses Grenzdefinitionsproblem aufzuschieben.

**iFay-↔-coFay-Kollaboration und -Delegation** — dies ist das Kernthema von Phase 4. Dieser Zeitraum führt die Protokollform der coFay-Aufsicht aus zwei Gründen nicht ein: Das Zuordnungsende eines coFay ist gewöhnlich eine Organisation oder eine Rolle, und wie eine Organisation die Aufsichtspflicht institutionell auf konkrete Personen oder Rollen niederbringt, ist selbst eine komplexe Diskussion über Institutionen, Recht und Corporate Governance hinweg; und die Protokollform für „Verantwortungsübergabe geht nicht verloren" in der Cross-Fay-Kollaboration braucht stabile Phasen 1 bis 3, bevor sie einen passenden Plug-in-Punkt hat.

**iFay-↔-iFay-Kollaboration** — wenn mehrere iFays (jeder einem anderen Human Prime zugeordnet) aufsichts-übergreifend zusammenarbeiten, um eine Handlung zu erfüllen, ergibt sich die Frage des „Mehr-Personen-Pfads der Übergabe der Handlungszuordnung": Sollte die Handlung dem Initiator, dem Empfänger oder beiden nach einer Aufteilungsregel zugeordnet werden? Diese Frage ähnelt dem rechtlichen Design „Untervollmacht zwischen Vertretern" in der realen Gesellschaft, doch die Hochfrequenzdichte der Kollaboration in der Fay-Ära macht die Verarbeitungsgeschwindigkeit traditionellen Rechts weit hinterherhinken. Dieses Thema braucht die simultane Evolution von Recht, Protokoll und gesellschaftlicher Governance, bevor eine stabile Antwort gefunden werden kann.

Die obigen vier Beziehungsarten gehören alle zu langfristigen Evolutionsrichtungen des Faying Protocol. Sie werden in den Phasen 2 bis 5 des Missionspfads progressiv aufgenommen, aber die Protokollform jeder einzelnen wird durch separate spätere Spezifikationen getragen und liegt außerhalb des Geltungsbereichs dieses Zeitraums.

## B4: Standortmeldung während Rogue

Punkt 4 der Dimension B in Kapitel 13 (B4) ist der einzige Protokoll-Designpunkt in diesem Blueprint, der ausdrücklich mit „Keine Schlussfolgerung in diesem Zeitraum" gekennzeichnet ist.

### Beschreibung des Themas

Wenn ein von einem iFay übernommenes Endgerät (z. B. eine Drohne) in Rogue Fay eintritt, soll es weiterhin aktiv seinen physischen Standort oder Endgerätezustand an den zuordnenden Human Prime melden?

Beispiel: Jacks Drohne verliert während einer Aufgabe die Verbindung zu Jack (erfüllt die Auslösebedingung 4 in Kapitel 13, „der Human Prime ist offline oder über einen längeren Zeitraum unerreichbar") und tritt in Rogue Fay ein. Der physische Standort der Drohne ändert sich noch — beeinflusst durch Trägheit, Wind, autonome Landealgorithmen und so weiter. Die Frage ist: Soll diese Drohne weiterhin aktiv ihre Position, ihren Akkustand und andere Endgerätezustände an Jacks Seite melden?

### Eine zweiseitige Spannung

**Pro fortgesetzte Meldung** — je mehr ein getrennter Fay meldet, desto leichter ist es für den Human Prime, ihn wiederzufinden und Faying neu herzustellen. Aus der Perspektive der Wiederherstellbarkeit ist „Standort ist sichtbar" eine Fähigkeit, die die Interessen des Human Prime schützt.

**Gegen fortgesetzte Meldung** — sobald ein Fay seinen Standort in Rogue weiter meldet, kann ein Angreifer diesen Kanal ausnutzen: Standortinformationen abfangen, um den Aktivitätsbereich des Human Prime zu erfassen; den Meldekanal fälschen, um die Seite des Human Prime zu imitieren und Fay-Handlungen herbeizuführen; „kontinuierliche Meldung" als Mittel zur Angriffsaufklärung nutzen.

Beide Seiten des Werts sind legitim, und beide passen zum inneren Geist von Human View, doch sie weisen auf entgegengesetzte Protokoll-Designentscheidungen. Im Rogue-Zustand von Rogue Fay kann „aktive Meldung" gleichermaßen den Human Prime schützen oder den Human Prime verraten.

### Mögliche Mittelwege

Mögliche Lösungen in der Zukunft umfassen die folgenden Denkrichtungen, sind aber nicht darauf beschränkt. Der Blueprint trifft unter ihnen keine Vorauswahl.

**Differenzierte Behandlung nach Rogue-Ursache** — Human Prime hat aktiv widerrufen → Standort verbergen; Verbindung verloren / Timeout → Standort offenlegen; Eindringalarm → Standort offenlegen. „Warum in Rogue eingetreten" als Kriterium dafür nutzen, ob gemeldet wird.

**Explizit per Vorautorisierung wählen** — zum Zeitpunkt der Initiierung der Faying Action den Human Prime ausdrücklich erklären lassen, „wenn ich anschließend die Verbindung verliere, ist es diesem Endgerät erlaubt, den Standort weiter zu melden?"

**Gestufte Meldung** — keinen präzisen Standort melden, sondern minimale Signale, die keine räumlichen Informationen preisgeben, wie „ich bin noch in Rogue, Gesundheit ist normal".

Keine dieser drei Denkrichtungen wird in diesem Zeitraum als Schlussfolgerung übernommen. Sie gehören zu Themen, die während der Evolution des Faying Protocol in Phasen 2 bis 5 gründlich diskutiert werden müssen und Eingaben von Privatsphäre-, Sicherheits- und regulatorischen Parteien aufnehmen sollten.

### Verhältnis dieses Themas zu Kapitel 13

B4 ist lediglich **zu diskutieren**, nicht **auszuführen**. Bevor das Protokollspezifikationsdokument eine endgültige Wahl für B4 landet, bleiben alle anderen von Kapitel 13 gegebenen Regeln — B1–B3 erlaubt, die vollständigen Regeln A1–A4, C1–C3, D1–D4 — vollständig in Kraft. Die faktische Position von B4 in diesem Zeitraum ist „die Protokollebene schreibt Implementierung weder vor noch verbietet sie", und überlässt die Entscheidung konkreten Implementierern und zukünftigen Spezifikationen.

## Ende des Blueprints

An diesem Punkt sollten Sie die folgenden drei Fragen zum Faying Protocol selbst beantworten können:

- **Was ist es?** Ein Vertrag, der zwischen Human Prime und Fay ausdrücklich ausspricht, „wie Kontrolle und Verantwortung übergeben werden".
- **Was trägt es heute?** Die ethische Untergrenze der Kapitel 11 bis 13 + die minimale Vertragsform von Phase 1.
- **Was trägt es noch nicht?** Alle in diesem Kapitel aufrichtig aufgezählten vorausschauenden Themen.

Ein Blueprint, der glaubt, jede Frage beantwortet zu haben, ist am ehesten dazu geneigt, beim Auftauchen neuer Szenarien Dinge aufzugeben, die nicht aufgegeben werden sollten. Ein Blueprint, der die offenen Fragen aufrichtig auflistet, ist im Gegenteil eher in der Lage, die Untergrenze durch zukünftige Erweiterungen unkompromittiert zu halten.
