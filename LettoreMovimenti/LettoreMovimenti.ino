#include <HCSR04.h>

// trig pin=2, echo pin=3

HCSR04 hc(2, 3);

const float sogliaIngresso = 5.0;
const float sogliaUscita = 2.0;

float distanzaIniziale = 0;
bool presenzaAttiva = false;

void inviaPacchetto(float distanza, String stato) {
  Serial.print("<DIST:");
  Serial.print(distanza, 2);
  Serial.print(",STATE:");
  Serial.print(stato);
  Serial.println(">");
}

void setup() {
  Serial.begin(9600);

  delay(1000);

  distanzaIniziale = hc.dist();

  //Serial.print("Distanza iniziale: ");
  //Serial.println(distanzaIniziale);
}

void loop() {
  float distanza = hc.dist();
  String stato = "NONE";

  if (distanza > 0) {
    if (!presenzaAttiva && distanza < (distanzaIniziale - sogliaIngresso)) {
      Serial.println("Presenza rilevata!");

      presenzaAttiva = true;
      stato = "RILEVATO";
    }

    if (presenzaAttiva && distanza >= (distanzaIniziale - sogliaUscita)) {
      Serial.println("Zona di nuovo libera");
      presenzaAttiva = false;
      stato = "LIBERA";
    }

    inviaPacchetto(distanza, stato);
  }

  delay(500);
}