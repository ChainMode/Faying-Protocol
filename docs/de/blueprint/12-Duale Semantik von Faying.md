# Duale Semantik von Faying

Mittlerweile ist das Wort „Faying" mehrfach aufgetaucht: als Name des Vertrags in Kapitel 2, als Unterscheidung zwischen iFay und Agent in Kapitel 3, als Träger der Werteanforderung Human View in Kapitel 11. Doch worauf sich Faying tatsächlich bezieht, wurde absichtlich bis hierher zurückgestellt. Der Grund ist, dass es sich nicht von einer einzigen Seite her beschreiben lässt.

Faying trägt zwei Semantiken zugleich.

**Zustands-Semantik** — der Verbindungszustand eines Fay unter der Aufsicht eines Human Prime, genannt **Faying State**.
**Aktions-Semantik** — die Handlung der „Übergabe der Kontrolle", durch die ein Fay aus dem Rogue-Zustand in den Faying State eintritt, genannt **Faying Action**.

Die beiden Semantiken sind untrennbar: Ohne eine Faying Action wird der Faying State nie hergestellt; ohne Faying State ist eine Faying Action nur eine leere Operation. Dies ist das **Prinzip der dualen Semantik** von Faying.

Jeder Versuch, Faying auf eine einzige Seite zu vereinfachen — es lediglich als „einen Verbindungszustand" oder lediglich als „eine Schalthandlung" zu nehmen — löscht still die Verantwortungszuordnung auf der Protokollebene aus.

## Faying State: der Verbindungszustand unter Aufsicht

Faying State ist der Verbindungszustand eines Fay unter der Aufsicht eines spezifischen Human Prime. Ein Fay, der in diesen Zustand eintritt, hat drei notwendige Eigenschaften.

**Handlungs-Zuordnung ist eindeutig** — alle nach außen gerichteten Handlungen des Fay in diesem Zustand werden diesem Human Prime zugeordnet. Ob die Handlung autonom vom Fay entschieden, vom Human Prime ausdrücklich befohlen oder durch die externe Umgebung ausgelöst wurde — das verantwortliche Ende springt nicht.

**Kontinuierliche Sichtbarkeit** — während dieses Zustands hält der Human Prime Human View über die Aktivität des Fay und kann jederzeit bestätigen, ob die Aufsicht noch wirksam ist.

**Der Interventionspfad ist stets offen** — während dieses Zustands haben Befehle des Human Prime zu Widerruf, Pause, Verlangsamung oder Zerstörung gegenüber dem Fay höchste Priorität. Der Fay darf diese Befehle nicht aus irgendwelchen „geschäftlichen Gründen" überschreiben.

Faying State ist kein statisches Ergebnis; es ist eine kontinuierlich online bestehende Verpflichtung. Sie muss in jedem mikroskopischen Moment neu bestätigt werden, nicht einmal hergestellt und für immer gehalten. Sobald irgendeine der drei obigen Eigenschaften nicht mehr hält, sollte der Faying State in den in Kapitel 13 definierten Beendigungsablauf eintreten.

> **Eine wichtige umgekehrte Folgerung**: Im Zustand außerhalb des Faying State (d. h. Rogue Fay) hat keine nach außen gerichtete Handlung eines Fay jemanden, der die Verantwortung empfängt. Daher ist die einzig akzeptable Designentscheidung, die das Faying Protocol auf der Protokollebene treffen kann: **dem Fay während Rogue Fay das Handeln zu verbieten**, statt „handeln zu lassen und Zuordnung nachträglich zu flicken". Dieses Prinzip wird in Kapitel 13 streng gelandet.

## Faying Action: die Übergabe der Kontrolle

Eine Faying Action ist eine spezifische, beobachtbare, auditierbare Handlung der „Übergabe der Kontrolle".

Die treffendste Analogie ist diese alltägliche Szene:

> Jack übergibt das Lenkrad eines Autos einem KI-Fahrer. In diesem Moment drückt Jack nicht einfach einen „Autopilot"-Knopf — er **übergibt die Kontrolle** auf eine für die Außenwelt klar wahrnehmbare Weise. Davor gehörte das Lenkrad Jack; danach gehört das Lenkrad jenem KI-Fahrer; gleichzeitig fallen alle Folgen, die aus dem Lenkrad entstehen, weiterhin auf Jack, der den Führerschein hält.

Eine Faying Action ist die entsprechende „Übergabe des Lenkrads" in der digitalen Welt. Sie bewegt einen Fay klar, bezeugbar und rückverfolgbar aus dem Rogue-Zustand des „Existieren-aber-nicht-Handeln-Könnens" in den Faying State des „Handeln-im-Namen-des-Human-Prime".

Daraus ergeben sich mehrere nicht verhandelbare Eigenschaften einer Faying Action.

**Muss ausdrücklich vom Human Prime initiiert werden** — eine Faying Action erlaubt es einem Fay nicht, selbst zu entscheiden, zu beginnen. Ein Fay darf nicht autonom in den Faying State eintreten, bloß weil „letztes Mal so begonnen wurde", „ich schließe, dass der Human Prime jetzt wünschen würde, dass ich beginne" oder „ich war zuvor für ähnliche Handlungen autorisiert". Jeder Eintritt muss ausdrücklich vom Human Prime initiiert werden.

**Muss bezeugbar sein** — eine Faying Action muss eine für die Außenwelt (einschließlich Auditoren, Regulierern, dem Fay selbst, anderen Fays und dem Human Prime) beobachtbare Spur hinterlassen. Eine nicht bezeugte Faying Action ist gleichbedeutend mit einer, die nicht stattfand.

**Muss einen begrenzten Geltungsbereich haben** — eine Faying Action sollte keine ewige „Vollmachts-Delegation" sein. Der Blueprint befürwortet stark, dass eine Faying Action einen ausdrücklichen Geltungsbereich (z. B. ein Zeitfenster, ein Aufgabenumfang, ein Endgerätegeltungsbereich) trägt und beim Erreichen der Grenze automatisch verfällt. Unbegrenztes Faying ist ein zu vermeidendes Anti-Muster.

**Muss symmetrisch widerruflich sein** — jede Faying Action muss einen entsprechenden, symmetrischen Widerrufspfad haben. Den Faying State herstellen und den Faying State verlassen müssen **zwei gleichermaßen erreichbare** Pfade sein, kein asymmetrisches Design „leicht zu öffnen, schwer zu schließen".

## Beide Seiten zusammen sind Faying

Stellt man Zustands- und Aktions-Seiten zusammen, lässt sich die volle Bedeutung von Faying in diesem Absatz ausdrücken:

> **Faying ist eine vom Human Prime ausdrücklich initiierte Handlung der „Übergabe der Kontrolle" (Faying Action), die bezeugbar und symmetrisch widerruflich ist und den Fay in einen kontinuierlich online bestehenden Verbindungszustand unter Aufsicht (Faying State) versetzt; innerhalb dieses Zustands darf der Fay im Namen des Human Prime handeln, und die Folgen werden allesamt von diesem Human Prime getragen; außerhalb dieses Zustands ist es dem Fay nicht erlaubt zu handeln.**

Derselbe Absatz ergibt drei Verpflichtungen entlang der Zeitdimension. **Vergangenheit**: Der Faying State wird stets durch eine spezifische Faying Action erreicht; es gibt keinen Fay, der „einfach von Natur aus in Faying ist". **Gegenwart**: Die Gültigkeit des Faying State wird in jedem Moment durch Human View kontinuierlich kalibriert, nicht einmal hergestellt und für immer gehalten. **Zukunft**: Der Faying State wird schließlich durch einen symmetrischen Widerruf oder ein automatisches Verfallen enden und den Fay in den in Kapitel 13 definierten Rogue-Zustand zurückführen.

## Harte Beschränkungen für das Protokolldesign

Dieses Kapitel als Werte-Kapitel spezifiziert keine Felder oder Nachrichten, legt aber dem konkreten Design des Faying Protocol mehrere nicht verhandelbare harte Beschränkungen auf:

- die Protokollebene muss erstklassigen Ausdruck für **beide** Seiten — Zustand und Aktion — bereitstellen; sie darf nicht nur eine Seite ausdrücken;
- die Protokollebene verbietet jeden legitimen Pfad, „durch den ein Fay eine Faying Action auf sich selbst initiiert";
- die Protokollebene muss für jede Faying Action eine bezeugbare Spur und einen symmetrisch widerruflichen Pfad bereitstellen;
- die Protokollebene verbietet „unbegrenztes Faying" als Standardform; sie muss erzwingen, dass eine Faying Action auf der Protokollebene einen begrenzten Geltungsbereich trägt;
- die Protokollebene muss garantieren: Wenn irgendeine Bedingung ausgelöst wird, unter der der Faying State nicht mehr hält, geht der Fay automatisch in den Rogue-Zustand über, nicht in ein „degradiertes Faying".

Wie eine Aufsichtsbeziehung hergestellt, aufrechterhalten und beendet wird, ist nun auf der Werte-Ebene vollständig definiert. Das nächste Kapitel kehrt die Perspektive um: Wenn der Faying State nicht hält, was darf der Fay und was darf er nicht? Es ist das strengste Kapitel dieses Blueprints, dasjenige, in dem keine Konzession erlaubt ist.
