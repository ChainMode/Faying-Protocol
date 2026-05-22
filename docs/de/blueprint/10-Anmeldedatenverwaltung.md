# Anmeldedatenverwaltung

Anmeldedatenverwaltung klingt stark nach Engineering — Ausstellung, Signierung, Widerruf und Erneuerung von FayID, jeweils mit spezifischen Algorithmen und Schlüsselprotokollen verbunden. Doch in diesem Blueprint ist die Anmeldedatenverwaltung den Werten zugeordnet, nicht den technischen Themen.

Der Grund ist dieser: Das Faying Protocol existiert, um „wem gehört die Handlung an" explizit zu machen. Der technische Träger davon ist beim Landen auf der konkreten Protokollebene das Anmeldedatum (credential). Das Anmeldedatum beantwortet zwei Fragen:

> **Ist dieser Fay, gerade jetzt, der Fay, der zu sein er behauptet?**
> **Ist dieser Fay, gerade jetzt, weiterhin von seinem Human Prime autorisiert?**

Keine ist eine ingenieurtechnische Frage; beide sind Verantwortungsfragen. Sobald Anmeldedaten gefälscht, missbraucht oder still durch Dritte außerhalb des Human Prime ausgestellt werden können, verschwindet der gesamte Wert des Faying Protocol augenblicklich — der Human Prime ist nicht länger der wahre Träger der Verantwortung.

Spezifische Algorithmen, Signaturformate, Schlüsselprotokolle und andere technische Details gehören in das Protokollspezifikationsdokument und das Schema; dieses Kapitel entfaltet sie nicht. Dieses Kapitel formuliert lediglich die wenigen Positionen zur Anmeldedatenverwaltung, bei denen kein Zugeständnis erlaubt ist.

## FayID ist die Identitätsgrundlage für den Eintritt in den Faying State

FayID ist die einheitliche, eindeutige Identität eines Fay innerhalb des iFay-Frameworks. Der gesamte Aufsichtsvertrag des Faying Protocol baut auf FayID auf. Eine Faying Action muss explizit machen „welche FayID in den Faying State eintritt"; die Zuordnung des Faying State muss explizit machen „welche FayID welchem Human Prime zugeordnet ist"; der Austritt aus dem Faying State muss explizit machen „welche FayID in Rogue Fay eintritt".

Wenn FayID nicht vertraut werden kann, verlieren alle drei obigen Urteile ihre Bedeutung.

## Anmeldedaten-Versagen ist gleich Faying-Versagen

Unter den neun in Kapitel 13 aufgelisteten Auslösebedingungen für den automatischen Übergang vom Faying State in Rogue Fay besagt Bedingung 6 ausdrücklich:

> **Die Identität des Fay kann nicht verifiziert werden (z. B. ist die FayID-Signatur abgelaufen).**

Dieser Punkt ist innerhalb der neun keine Eintrag, der „zufällig Anmeldedaten betrifft"; er ist die konkrete Landung der Anmeldedatenverwaltung auf der Protokollebene, die nicht umgangen werden darf. Sobald die Gültigkeit der FayID in Frage steht — egal wie kontinuierlich oder beinahe vollständig die vorherige Arbeit des Fay war — muss der Faying State sofort enden:

> **Ein Zweifel an der Anmeldedaten-Gültigkeit ist gleichbedeutend damit, dass der Faying State bereits versagt hat.**

Es gibt keinen Zwischenfall „Anmeldedatum ist verdächtig, aber Faying State hält noch", und es gibt keinen ingenieurtechnischen Kompromiss „erst die aktuelle Aufgabe abschließen und dann das Anmeldedaten-Problem behandeln".

## Widerrufsrechte müssen auf der Seite des Human Prime bleiben

Anmeldedatenverwaltung hat einen scheinbar geringfügigen, aber äußerst kritischen Trade-off im Protokolldesign — wem gehört letztlich der Widerruf eines Anmeldedatums? Die Antwort ist offensichtlich: dem Human Prime.

Der Fay selbst sollte keinen legitimen Pfad haben, sein eigenes Anmeldedatum zu widerrufen — homolog zu D4 in Kapitel 13 kann ein Fay nicht selbst entscheiden, die Aufsicht zu verlassen, noch kann er selbst entscheiden, das Aufsichtsband zu durchtrennen.

Drittanbieter-Plattformen, die Runtime-Anbieter des Fay und die Fähigkeitsanbieter des Fay dürfen ohne Zustimmung des Human Prime nicht die Macht haben, dessen FayID zu widerrufen — es sei denn, dieser Dritte ist eine zuständige Behörde im regulatorischen Sinne (siehe Auslösebedingung 8 in Kapitel 13).

Der Human Prime muss stets einen symmetrischen, erreichbaren, auditierbaren Widerrufspfad behalten. Die Erreichbarkeit der Widerrufshandlung darf nicht geringer sein als die Erreichbarkeit der Initiierung einer Faying Action. Dies ist die konkrete Landung des „Symmetrie"-Prinzips des Faying Protocol auf der Anmeldedatenebene: Aufsicht herstellen und Aufsicht widerrufen müssen zwei gleichermaßen erreichbare Pfade sein. Sobald Widerruf schwerer wird als Etablierung, gleitet die Aufsichtsbeziehung faktisch in Richtung „unwiderrufliche Delegation" und verletzt damit die Anforderung „der Interventionspfad ist stets offen" von Human View.

## Erneuerung ist kein Standardverhalten

Kapitel 12 legt eine harte Beschränkung für den Faying State fest: Ein Faying State muss einen begrenzten Geltungsbereich haben, und unbegrenztes Faying ist ein Anti-Muster. Die diesem Constraint auf Anmeldedatenebene entsprechende Position ist — die Erneuerung eines Anmeldedatums sollte nicht standardmäßig erfolgen.

Jede Erneuerung sollte eine ausdrückliche, bezeugbare Handlung sein, keine implizite Schleife „Fay reicht automatisch ein, das System erneuert automatisch". Der Blueprint erlaubt ingenieurtechnische Bequemlichkeiten wie „Erneuerungserinnerungen" und „Erneuerungsvorschläge", verbietet aber, „Erneuerung" zu etwas zu machen, was der Fay still selbst abschließen kann — das würde Faying faktisch in unbegrenzte Delegation verwandeln.

Aus der Verantwortungsperspektive verstanden: Erneuerung ist der Moment, in dem das verantwortliche Ende die Aufsichtsabsicht erneut ausdrückt. Wenn selbst die Erneuerung still durch Engineering abgeschlossen wird, bleibt von „Aufsicht" nur eine Signatur und keine Absicht.

## Einige unverletzliche rote Linien

Die wenigen Werte-Positionen der Anmeldedatenverwaltung sind rote Linien, die keine technische Lösung beim Landen verletzen darf:

- FayID ist die Identitätsgrundlage;
- ein Anmeldedatum, dem nicht vertraut werden kann, bedeutet, dass Faying nicht hält;
- Widerrufsrechte müssen auf der Seite des Human Prime bleiben;
- Erneuerung ist kein Standardverhalten.

Konkrete Signaturalgorithmen, Schlüsselhierarchien, Verbreitung von Widerrufslisten, feinkörniges Design der Erneuerungszeitfenster, die Struktur von Wurzelzertifikaten für herstellerübergreifendes Mutual Trust und die endgültige Konsistenz von Widerrufen — diese technischen Details gehören in die Protokollspezifikation. Dieses Kapitel wiederholt und entscheidet sie nicht vorab, doch jede technische Lösung muss zuerst die vier obigen Positionen einhalten.

![Illustration der Anmeldedatenverwaltung: Kontrolle über FayID, Signierung, Widerruf und Erneuerung auf der Seite des Human Prime](../../zh-CN/blueprint/illustration/credential-management.png)
