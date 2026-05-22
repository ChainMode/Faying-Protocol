# Position des iFay-Frameworks

Dieses Kapitel beantwortet nur zwei Fragen: Wie sieht das iFay-Framework grob aus, und wo sitzt das Faying Protocol darin?

Das iFay-Framework selbst hat eine breite Abdeckung und viele Komponenten; jede einzelne führt, auch nur leicht entfaltet, in technische Details von Feldern, Protokollen und Nachrichtenformaten. Die drei Asset-Kategorien in diesem Repository — Blueprint, Protokollspezifikation und Schema — tragen ausschließlich das Faying Protocol. Alle Mitglieder der iFay-Protokollfamilie außer dem Faying Protocol werden einheitlich durch Verlinkung auf [ifay.ai](https://ifay.ai) referenziert; dieses Repository wiederholt, schreibt sie nicht um und leitet sie nicht ab.

## Umriss des iFay-Frameworks

Folgt man dem Gesamtdesign auf [ifay.ai](https://ifay.ai), lässt sich das iFay-Framework grob als vierschichtige Struktur verstehen.

**Die Entitätsebene** enthält zwei Arten intelligenter Entitäten, die durch das Protokoll gebunden sind. **iFay** (Individual Fay) ist zwingend eins-zu-eins an einen spezifischen Human Prime gebunden — entzieht man diese Zuordnung, ist es kein iFay mehr. **coFay** ist ein geteilter Fay; sein Betrieb ist nur erlaubt, wenn er ausdrücklich einer Person oder Organisation mit der rechtlichen Fähigkeit, Verantwortung zu tragen, zugeordnet ist. Ob iFay oder coFay — das in diesem Blueprint behandelte Faying Protocol bindet sie gleichermaßen: Sobald die Zuordnung verfällt, muss der Fay stoppen.

**Die Kernkomponenten** umfassen mehrere untrennbare Teile im Inneren jeder Fay-Entität. **FayID** ist die einheitliche, eindeutige Identität eines Fay, die Identitätsgrundlage für den Eintritt in jede Aufsichtsbeziehung. **Ego** ist das auf das Profil einer spezifischen Person oder Rolle abgestimmte Basis-Paradigma, das den autonomen Spielraum des Fay entlang Werteorientierung, Interessenpräferenzen, Gewohnheiten, kognitiven und Fähigkeitsgrenzen, Berechtigungsgrenzen und Arbeitsstil einschränkt. Ego ist kein gigantisches AGI-Modell; es ist eine „Persönlichkeitsgrenze". **Runtime** ist die virtuelle Laufzeit eines Fay, die es iFay und coFay erlaubt, kompatibel über verschiedene Endgeräte, Betriebssysteme und eingebettete Anwendungsszenarien hinweg zu laufen. FayID und Ego sind die beiden Voraussetzungen, die das Faying Protocol wirksam werden lassen — Ersteres trägt die Identitätszuordnung, Letzteres trägt die Verhaltensgrenze.

**Die Protokollfamilie** umfasst eine Reihe von Protokollen, mit denen ein iFay sich mit der Welt verbindet, sie wahrnimmt und mit ihr zusammenarbeitet. Jenseits des Themas dieses Blueprints, des **Faying Protocol**, gehören dazu mindestens: bidirektionale Transportprotokolle für Endgerätesteuerung, UI-freundliche Protokolle für menschliche Benutzeroberflächen, semantische Kommunikationsprotokolle zwischen iFay und coFay, die die UI-Übersetzungsschicht abstreifen, Broadcast-und-Subscribe-Protokolle für cloud-seitige Fähigkeiten und alle künftigen Mitglieder. Technische Details der Protokollfamilie finden Sie auf [ifay.ai](https://ifay.ai); dieses Repository nimmt sie nicht auf.

**Die Wertstruktur** entspricht einem neuen Modell der Arbeitsstruktur und Wertverteilung. Diese Schicht enthält systemische Verschiebungen: das Ausscheiden menschlicher Arbeit aus der Erwerbsarbeit, die Verflachung des Wissens, universelle Existenzsicherung, neue Wertschöpfung, neue gesellschaftliche Schichtung — mit Mechanismen wie MeriToken, die die Wertmessung tragen. Dies ist der langfristige Hintergrund des iFay-Frameworks; es landet nicht direkt auf der Faying-Protocol-Spezifikation. Details siehe [ifay.ai](https://ifay.ai).

## Die Position des Faying Protocol darin

Stellt man die vier Schichten zusammen, lässt sich die Position des Faying Protocol im iFay-Framework präzise wie folgt verankern:

> **Das Faying Protocol sitzt oberhalb der „Entitätsebene" und der „Kernkomponenten" und ist das Sub-Protokoll innerhalb der Protokollfamilie, das für die Semantik „Kontrolle unter Aufsicht und delegierte Kontrolle" zuständig ist. Es verwandelt die Wurzelfrage — „ist FayID einem Human Prime zugeordnet" — in eine Reihe von Verbindungszuständen und Aktionen, die hergestellt, aufrechterhalten und widerrufen werden können.**

Es ist keine Definition der Fay-Fähigkeit, also legt es nicht fest, was ein Fay tun kann. Es ist kein Verhaltenskodex eines Fay, also legt es nicht fest, wie ein Fay etwas tun soll. Es beantwortet nur eine Frage:

> **Für die Handlung dieses Fay, gerade jetzt, wer ist verantwortlich?**

Aus diesem Grund ist das Faying Protocol weder das blendendste noch das tiefgründigste Protokoll im iFay-Framework, aber es ist dasjenige, das nicht übersprungen werden darf. Sobald es fehlt, degeneriert das gesamte iFay-Framework sofort zu einem gewöhnlichen Agent-Ökosystem und trägt das in Kapitel 1 beschriebene Verantwortungsvakuum in die Gesellschaft.

## Grenze zwischen diesem Repository und dem iFay-Framework

```
                 +-------------------+
                 |   ifay.ai panorama |
                 |   iFay framework   |
                 |     (four layers)  |
                 +-------------------+
                          │
                          │  This repo unfolds one member
                          ▼
            +---------------------------+
            |   Faying Protocol project  |
            |   (all assets of this repo)|
            +---------------------------+
                          │
            ┌─────────────┼──────────────┐
            ▼             ▼              ▼
        Blueprint    Protocol Spec      Schema
   docs/{lang}/    docs/{lang}/         schema/
    blueprint/    specification/   (not delivered this period)
   (this spec)  (later, separate spec)
```

Alle drei Asset-Kategorien dieses Repositorys tragen ausschließlich das Faying Protocol. Eine eingehende Entfaltung anderer Mitglieder des iFay-Frameworks liegt außerhalb des Geltungsbereichs dieses Repositorys; gehen Sie bitte direkt zu [ifay.ai](https://ifay.ai).

![Übersicht iFay-Framework (alpha1): Das Faying Protocol sitzt auf der Vertragsebene der Aufsichtsbeziehung](../../zh-CN/blueprint/illustration/ifay-framework-alpha1.png)

![iFay-Titelbanner](../../zh-CN/blueprint/illustration/ifay-title-banner.png)
