# Phase 3: Abgeleitete Übernahme von Softwareanwendungen durch iFay

Phase 3 wendet die Erweiterungsrichtung von Endgerät-Hardware zu Softwareanwendungen — lokale Anwendungen, Cloud-Dienste und In-APP eingebettete Szenarien.

Es gibt einen entscheidenden Unterschied zwischen Softwareanwendungen und Hardware-Endgeräten: Der Zustand eines Hardware-Endgeräts ist relativ konzentriert — eine Drohne oder ein Roboter ist ein einzelnes Objekt unter Aufsicht — während die Grenze einer Softwareanwendung oft prozessbasiert, modular und netzwerkübergreifend ist. Ein E-Commerce-Client, der von einem iFay übernommen wird, kann gleichzeitig über mehrere Domänen, mehrere APIs und mehrere Drittanbieterdienste hinweg zusammenarbeiten. Die Schwierigkeit von Phase 3 liegt nicht in „der Übernahme", sondern darin, ob die Grenze der Übernahme klar beschrieben ist.

## Mit Phase 2 strukturhomologe Ableitung

Phase 3 ist strukturell symmetrisch zu Phase 2 und führt ebenfalls „Human Prime ↔ Softwareanwendung" nicht als direkte Beziehung ein:

> **Die Softwareanwendung tritt durch den iFay des entsprechenden Human Prime in den Faying State ein.**

Das verantwortliche Ende ist nach wie vor der Human Prime. Der iFay übernimmt die Softwareanwendung abgeleitet durch den Faying State; der Mechanismus ist homolog zu dem der Endgeräteübernahme in Phase 2. Die Softwareanwendung selbst steht nicht eigenständig im Faying State.

## Drei Schlüsselunterschiede

Phase 3 fügt drei zusätzliche Komplexitäten hinzu, die auf Phase 2s Struktur besondere Behandlung erfordern.

**Feinere Übernahmegranularität**. Ein iFay kann nur einen Teil der Softwarefunktionen übernehmen — beispielsweise darf er im Namen anderer bestellen, aber nicht die Sicherheitsrichtlinie des Kontos ändern. Phase 3 muss daher feinkörnigere „Übernahmebereiche" auf Protokollebene ausdrücken, homolog zum Prinzip in Kapitel 12, dass „eine Faying Action einen begrenzten Geltungsbereich haben muss".

**Dichtere grenzüberschreitende Kollaboration**. Die übernommene Software kann intern mehrere externe Dienste, Drittanbieter-APIs und entfernte Cloud-Funktionen aufrufen. Phase 3 muss sicherstellen, dass jeder durch die übernommene Software vom iFay initiierte Aufruf seine Verantwortung weiterhin dem ursprünglichen Human Prime zuordnet; Verantwortung darf entlang der dienstübergreifenden Aufrufkette nicht still entweichen. Diese Anforderung beantwortet direkt den in Kapitel 1 skizzierten realen Schmerzpunkt — „niemand kann klar sagen, welche Parteien Daten entlang der Aufrufkette verarbeiten".

**Heimlichere Nebenwirkungen**. Im Vergleich zu physischen Handlungen sind Software-Nebenwirkungen (Datenschreibvorgänge, Abonnementänderungen, Drittanbieter-Kontoverknüpfungen) für einen Human Prime intuitiv schwerer wahrzunehmen. Phase 3 muss die Anforderung der „Informationszugänglichkeit" aus dem Human View in Kapitel 11 expliziter landen — Nebenwirkungen müssen so offengelegt werden, dass der Human Prime sie zu vertretbaren Kosten erfahren kann, statt tief in der Aufrufkette begraben zu werden.

## Verhältnis zum Geltungsbereich des aktuellen Zeitraums

**Phase 3 liegt außerhalb des Geltungsbereichs des aktuellen Faying-Protokoll-Designs.** Dieses Kapitel skizziert die Existenz von Phase 3, um die Evolutionsrichtung des Faying Protocol zu erläutern, nicht um sich zu deren Auslieferung in diesem Zeitraum zu verpflichten. Die konkrete Protokollform von Phase 3 wird durch eine separate spätere Spezifikation getragen.

Nach Phase 3 deckt das Faying Protocol Fays Beziehung sowohl zu Hardware- als auch zu Software-Ausführungsenden ab, doch die Diskussion dreht sich noch immer um „einen Human Prime + einen iFay". Die nächste Stufe, Phase 4, weitet die Perspektive auf Organisationen: Wenn es mehr als einen Fay gibt und das verantwortliche Ende keine einzelne natürliche Person mehr ist, wie hält die Faying-Beziehung dennoch eine konsistente Zuordnung aufrecht?

![Phase-3-Konzept](../../zh-CN/blueprint/illustration/phase3-concept.png)

![Phase-3-Architektur](../../zh-CN/blueprint/illustration/phase3-architecture.png)
