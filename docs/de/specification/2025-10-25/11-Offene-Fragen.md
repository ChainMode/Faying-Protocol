---
title: "Faying Protocol/1.0 — §11 Offene Fragen"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: de
part: "Kapitel 11 von 11 (Protokolltext)"
---

> Protokolltext-Navigation: [Inhaltsverzeichnis](./README.md) | vorheriges [§10 Fehlerbehandlung](./10-Fehlerbehandlung.md) | nächstes [Anhang A Terminologie-Abgleich](./Anhang-A-Terminologie-Abgleich.md)

## §11 Offene Fragen

> Dieses Kapitel zählt aufrichtig Themen auf, die im Protokolltext der Phase 1 nicht zwingend beantwortet werden müssen, sondern dem Protocol Committee zur Klärung im RFC-Stadium überlassen bleiben. Jedes Thema liefert die **aktuelle Protokollneigung**, die **Alternativen** und den **Klärungsstatus**, damit nachfolgende RFC-Diskussionen einen strukturierten Ausgangspunkt haben. Geklärte Einträge (z. B. Q10 Protokollbenennung) werden als historischer Datensatz bewahrt.

### Q1 Endgeräte-Standortmeldung während des Rogue-Zustands

- **Thema**: Darf das Endgerät, während sich die iFay in Rogue Fay befindet, weiterhin den physischen Standort melden? Betrifft das beidseitige Spannungsfeld „Privatsphäre vs. Wiederherstellbarkeit“.
- **Aktuelle Protokollneigung**: Nach `RevokeReason` differenzieren — `human-initiated` / `task-completed` melden nicht; `fay-credential-invalid` / `regulatory-order` / `terminal-disconnected` usw. dürfen melden.
- **Alternativen**: (a) pauschales Verbot; (b) pauschale Erlaubnis; (c) der HP wählt zum BOOTSTRAP-Zeitpunkt ausdrücklich vorab.
- **Klärungsstatus**: offen; das Blueprint-Kapitel 14 trifft hierzu bereits ausdrücklich keine Schlussfolgerung.

### Q2 Nicht-ablehnbarer Pfad des G0 Emergency Override

- **Thema**: Wie lässt sich in Extremfällen, in denen die IF von einem Angreifer kompromittiert wurde, sicherstellen, dass die G0-Nachricht dennoch vom IF-Kern ausgeführt wird?
- **Aktuelle Protokollneigung**: Die Protokollebene schreibt vor, dass G0-Nachrichten höchste Priorität haben (siehe §7.2 / P12 G0-Override-Priorität), erkennt aber an, dass rein protokollseitige Mittel unzureichend sind, wenn der IF-Kern kompromittiert ist.
- **Alternativen**: (a) Hardware-Ebenen-Kill-Switch-Erzwingung; (b) TPM-Quote-Doppelsignatur-Bestätigung; (c) Protokollebene-Erzwingung beibehalten und den Hardware-Pfad der Ökosystem-Implementierungsfreiheit überlassen.
- **Klärungsstatus**: offen; tief mit der Endgeräteübernahme in Phase 2 / Phase 3 gekoppelt.

### Q3 PQC-Standardzeitplan

- **Thema**: Wann wird der Ed25519 + ML-DSA-65 Hybrid von OPTIONAL zu MUST hochgestuft?
- **Aktuelle Protokollneigung**: 1.0 deklariert nur OPTIONAL (PQC-Verhandlungs-Slots in §6.1); der Zeitplan wird festgelegt, nachdem alle NIST-Endstandards veröffentlicht sind.
- **Alternativen**: (a) auf die Finalisierung aller NIST-PQC-Standards warten; (b) dem ersten standardisierten Signaturalgorithmus folgen; (c) nach Stufe differenzieren (hochsensible Szenarien zuerst MUST).
- **Klärungsstatus**: offen; abhängig vom Fortschritt der NIST-PQC-Standardisierung.

### Q4 Cross-Human-Prime iFay ↔ iFay Kooperation (Phase 4/5)

- **Thema**: Wenn zwei iFays kooperieren, die zu verschiedenen HPs gehören, wie wird die Verantwortungsübertragung bestimmt?
- **Aktuelle Protokollneigung**: 1.0 deckt dies nicht ab; festzulegen in Phase 4, wenn coFay eingeführt wird.
- **Alternativen**: (a) Initiator trägt; (b) Empfänger trägt; (c) nach Regeln geteilt; (d) beide HPs müssen mitbezeugen.
- **Klärungsstatus**: offen; erfordert eine zweigleisige Diskussion von Recht und Protokoll.

### Q5 Objektive Bestimmung der Ego-Abweichung

- **Thema**: Sollte die Protokollebene den minimalen Entscheidungssignal-Satz für `ego-deviation` festlegen?
- **Aktuelle Protokollneigung**: Die Protokollebene definiert nur die Semantik von `RevokeReason="ego-deviation"` und die Konsequenzen der Auslösung (§EH.1, §3.6 BBS); der konkrete Entscheidungssignal-Satz bleibt der Implementierungsfreiheit überlassen.
- **Alternativen**: (a) Protokollebene schreibt den minimalen Signalsatz vor; (b) ausdrücklich durch den Behavior Baseline Service aus §3.6 beschränkt; (c) die aktuelle Offenheit beibehalten.
- **Klärungsstatus**: offen; gekoppelt mit Q13 Baseline-Standardisierung.

### Q6 Mandate-Erneuerungsrichtlinie

- **Thema**: Sollte das Protokoll alle Formen der „automatischen Erneuerung“ verbieten?
- **Aktuelle Protokollneigung**: alle automatischen Erneuerungsformen verbieten; jede Erneuerung muss eine ausdrückliche HP-Bezeugung durchlaufen (Neigung des Blueprint-Kapitels 10).
- **Alternativen**: (a) „begrenzte automatische Erneuerung mit erforderlicher periodischer HP-Vorsignatur“ erlauben; (b) automatische Erneuerung auf risikoarmen Stufen (G3/G4) erlauben; (c) Verbot beibehalten.
- **Klärungsstatus**: offen; abhängig von einem Beschluss des Protocol Committee.

### Q7 Offline- / Schwachnetz-Umgebung

- **Thema**: Ist in Edge-Szenarien, in denen die RR unerreichbar ist (Drohnen-Trennung), ein abgeschwächter Modus „zeitlich begrenzte Autonomie + Abgleich bei Wiederverbindung“ erlaubt?
- **Aktuelle Protokollneigung**: „zeitlich begrenzte Autonomie + Wiederverbindungs-Abgleich“ ausdrücklich über das Endorsed_Mandate modellieren (§7.5, §9.8, §4.3 Disconnected); Nicht-Endorsed-Pfade strikt Default-Deny (siehe P17.2 pessimistische Annahme).
- **Alternativen**: (a) sich allein auf das Endorsed_Mandate verlassen; (b) einen „regionalen RR-Cache“ einführen; (c) strikter Default-Deny ohne jede Ausnahme.
- **Klärungsstatus**: teilweise geklärt (Endorsed_Mandate bereits in §7.5 gelandet); die Offline-Richtlinien-Obergrenze erwartet die Klärung von Q11.

### Q8 Sub-Agent-„Ergänzungsstufe“

- **Thema**: Ist das fünfstufige System aus G0 Emergency_Override und G1 Strict / G2 Moderate / G3 Loose / G4 Autonomous ausreichend?
- **Aktuelle Protokollneigung**: 1.0 behält die fünf Stufen (§7.1); führt keine Zwischenstufen wie G2.5 ein.
- **Alternativen**: (a) eine „semi-autonome + unterbrechbare“ Zwischenstufe einführen; (b) Implementierungen erlauben, eigene Unterstufen zu definieren, die aber auf eine der fünf zurückgemappt werden; (c) orthogonale Endorsement-Grades-Unterstufen einführen (bereits in §7.5 gelandet).
- **Klärungsstatus**: teilweise geklärt (Endorsement Grades überlagern G1–G4 orthogonal); Zwischenstufen bleiben Open.

### Q9 Grenze der Widerrufs-Kaskade

- **Thema**: Wie wird die Sichtbarkeit des Kaskaden-Widerruf-Defaults von DELEGATE (`cascade=true`) unter mehrstufiger Ableitung gewährleistet?
- **Aktuelle Protokollneigung**: Default `cascade=true` (§5.3.5); Sichtbarkeit beschränkt durch `RevocationVisibilityBudget` (§9.7, P14 ableitungsübergreifender Kaskaden-Widerruf).
- **Alternativen**: (a) das Budget nach der Tiefe des Ableitungsbaums differenzieren; (b) ein einzelnes Budget + Push-/Pull-Zweigleisigkeit beibehalten.
- **Klärungsstatus**: offen; abhängig von Konformitätstests zur Messung der Sichtbarkeit tiefer Ableitungsbäume.

### Q10 Protokollbenennung (Geklärt)

- **Thema**: offizielle Protokollbenennung.
- **Klärungsergebnis**: Das Protokoll heißt offiziell **Faying Protocol** (keine eigene Abkürzung), Version `Faying Protocol/1.0`.
- **Klärungsstatus**: geklärt; dieses Thema bleibt als historischer Datensatz und steht nicht mehr zur Diskussion offen.

### Q11 Maximale Lebensdauer-Obergrenze des Endorsement

- **Thema**: Sollte die Protokollebene die harte Obergrenze von `endorsement.endorsed_lifetime` festlegen (z. B. ≤ 12 h)? Sollte sie weiter nach Stufe verschärft werden?
- **Aktuelle Protokollneigung**: Anhang B gibt einen empfohlenen Wert (Standard 4 h, weiche Obergrenze 12 h, und darf `Mandate.not_after − Mandate.not_before` nicht überschreiten; siehe P16.3 / P16.4); die harte Obergrenze erwartet eine RFC-Klärung.
- **Alternativen**: (a) eine 12-h-Obergrenze auf Protokollebene fest kodieren; (b) nach Stufe differenzieren (z. B. G1 ≤ 1 h, G4 ≤ 24 h); (c) den empfohlenen Wert nicht-zwingend beibehalten.
- **Klärungsstatus**: offen; gekoppelt mit Q7 Offline-Richtlinie.

### Q12 Missbrauchsschutz für bidirektionales Faying

- **Thema**: Sollte die iFay-initiierte `FAYING_REQUEST` einem zwingenden Rate-Limiting auf Protokollebene unterliegen (höchstens N-mal pro Minute je Paar (HP, IF))? Sollte das Rate-Limit in dasselbe `ConfirmationRateLimit`-Budget einbezogen werden?
- **Aktuelle Protokollneigung**: Die FAYING_REQUEST-Frequenz wird in dasselbe `ConfirmationRateLimit`-Budget einbezogen (siehe §5.3.6, §9.10.7, P18.6); ein Überschreiten löst eine Auto-Herabstufung / -Suspendierung gemäß §9.10.7 aus.
- **Alternativen**: (a) ein unabhängiges Budget `FayingRequestRateLimit`; (b) Budgets nach Stufe differenzieren; (c) die aktuelle Teilung mit ConfirmationRateLimit beibehalten.
- **Klärungsstatus**: teilweise geklärt (das standardmäßig geteilte Budget ist bereits in §9.10.7 gelandet); die Schwellenwert-Obergrenze und die Frage, ob das Budget unabhängig sein sollte, erwarten eine RFC-Klärung.

### Q13 Behavior_Baseline-Standardisierung

- **Thema**: Sollte die Kalibrierungsgranularität der Verhaltens-Baseline (nach `action` / `scope_used` / `risk_level` / `affected_resources` oder multidimensional gemeinsam) auf der Protokollebene einheitlich festgelegt werden? Oder sollten Implementierungen Freiheit haben, während verlangt wird, dass die Baseline-Kalibrierung selbst in die Attestation Chain geschrieben wird?
- **Aktuelle Protokollneigung**: Implementierungsfreiheit + Baseline-Kalibrierung in die Attestation Chain geschrieben; Kalibrierungsänderungen werden als Audit-Ereignisse behandelt (§3.6 I-BBS-3 / P18.5).
- **Alternativen**: (a) Protokollebene-Erzwingung (multidimensional gemeinsam über action / scope_used / risk_level / affected_resources); (b) Freiheit + Audit beibehalten; (c) eine „Baseline-Schema-Registry“ einführen, um die Kalibrierung zu vereinheitlichen.
- **Klärungsstatus**: offen; gekoppelt mit Q5 ego-deviation-Bestimmung.

### Q14 Objektive Kriterien für die Atomic_Action-Mindestgranularität

- **Thema**: Was ist die objektive Bestimmung der „minimalen unteilbaren Aktion“ auf Protokollebene? Sollte ein „Action-Lattice“ eingeführt werden, sodass `scope.actions` und die RP-seitige Aktionsmenge eine formalisierbare Reduktion auf minimaler Granularität haben?
- **Aktuelle Protokollneigung**: Die Protokollebene schreibt nur „genau 1 Atomic_Action pro Aufruf / `scope.actions` erlaubt keine Wildcards“ vor (P18.2 Atomic_Action_Strict); die objektive Bestimmung der Mindestgranularität bleibt den RPs und dem Protocol Committee gemäß branchen-/domänenspezifischen Konventionen überlassen.
- **Alternativen**: (a) ein RP-übergreifendes allgemeines Action-Lattice einführen; (b) separate Lattices je RP-Branche (Finanzen / Gesundheit / IoT) einführen; (c) die aktuelle Offenheit beibehalten.
- **Klärungsstatus**: offen; in Verbindung mit dem Erweiterungs-Slot T7 aus §9.10.8 diskutiert.

---
