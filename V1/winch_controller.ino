/*
  Motorized Pool-Cover Winch - controller firmware (Arduino Nano / ATmega328P)
  Matches Motor_Wiring_Diagram.svg

  Driver: brushed-DC driver in PWM + DIR mode (e.g. Cytron MDDS30, "PWM independent" mode)
  Safety (hardware): key switch + box E-stop + pendant E-stop drop the main contactor,
                     which cuts power to the motor driver AND this board.
  Safety (firmware): hold-to-run, soft start/stop, overcurrent trip, rope-in limit,
                     low-battery lockout, direction-change dwell, max run-time watchdog.
*/

// ---------------- pins ----------------
const uint8_t PIN_PWM     = 9;   // -> driver PWM
const uint8_t PIN_DIR     = 8;   // -> driver DIR
const uint8_t PIN_BTN_IN  = 2;   // pendant IN  (N.O. to COM/GND)
const uint8_t PIN_BTN_OUT = 3;   // pendant OUT (N.O. to COM/GND)
const uint8_t PIN_LIMIT   = 4;   // rope-in limit, N.C. to GND (HIGH = limit reached or wire broken)
const uint8_t PIN_BUZZER  = 5;
const uint8_t PIN_LED     = 6;   // pendant status LED (via 330 ohm)
const uint8_t PIN_ISENSE  = A0;  // ACS758-050B output
const uint8_t PIN_VBATT   = A1;  // 100k / 15k divider

// ---------------- tuning ----------------
const float   ACS_MV_PER_A     = 40.0;    // ACS758LCB-050B
const float   TRIP_AMPS        = 18.0;    // ~500 lbf rope pull with this gear train
const uint16_t TRIP_MS         = 300;     // must exceed TRIP_AMPS this long to trip
const float   VBATT_DIV        = (100.0 + 15.0) / 15.0;
const float   VBATT_MIN        = 22.0;    // LiFePO4 8S under load - refuse to start below this
const uint8_t PWM_MAX_IN       = 255;     // full speed winding in
const uint8_t PWM_MAX_OUT      = 200;     // pay out a little slower
const uint16_t RAMP_MS         = 500;     // soft start 0 -> max
const uint16_t REVERSE_DWELL_MS= 400;     // must be stopped this long before changing direction
const uint32_t MAX_RUN_MS      = 8UL * 60UL * 1000UL;  // watchdog: no single run longer than 8 min
const bool    DIR_IN_LEVEL     = HIGH;    // flip if the drum turns the wrong way when you press IN

enum State { IDLE, RUN_IN, RUN_OUT, FAULT };
State state = IDLE;
float acsZeroV = 2.5;
uint8_t pwmNow = 0;
uint32_t runStart = 0, overSince = 0, stoppedAt = 0;
int8_t lastDir = 0;
const char* faultMsg = "";

float readVolts(uint8_t pin) { return analogRead(pin) * (5.0 / 1023.0); }

float motorAmps() {
  long acc = 0;
  for (uint8_t i = 0; i < 8; i++) acc += analogRead(PIN_ISENSE);
  float v = (acc / 8.0) * (5.0 / 1023.0);
  return fabs((v - acsZeroV) * 1000.0 / ACS_MV_PER_A);
}

float battVolts() { return readVolts(PIN_VBATT) * VBATT_DIV; }

bool pressed(uint8_t pin) {          // debounced active-low read
  if (digitalRead(pin) == HIGH) return false;
  delay(3);
  return digitalRead(pin) == LOW;
}

void setMotor(int8_t dir, uint8_t pwm) {
  if (dir != 0) digitalWrite(PIN_DIR, dir > 0 ? DIR_IN_LEVEL : !DIR_IN_LEVEL);
  analogWrite(PIN_PWM, pwm);
  pwmNow = pwm;
}

void stopMotor() {
  // quick ramp-down so the worm gear doesn't shock-load
  while (pwmNow > 0) { pwmNow = pwmNow > 25 ? pwmNow - 25 : 0; analogWrite(PIN_PWM, pwmNow); delay(10); }
  noTone(PIN_BUZZER);
  if (state == RUN_IN || state == RUN_OUT) stoppedAt = millis();
  state = (state == FAULT) ? FAULT : IDLE;
}

void fault(const char* why) {
  state = FAULT; faultMsg = why;
  stopMotor();
  Serial.print(F("FAULT: ")); Serial.println(why);
  for (uint8_t i = 0; i < 3; i++) { tone(PIN_BUZZER, 2000, 150); delay(250); }
}

void setup() {
  pinMode(PIN_PWM, OUTPUT); analogWrite(PIN_PWM, 0);
  pinMode(PIN_DIR, OUTPUT);
  pinMode(PIN_BTN_IN, INPUT_PULLUP);
  pinMode(PIN_BTN_OUT, INPUT_PULLUP);
  pinMode(PIN_LIMIT, INPUT_PULLUP);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  Serial.begin(115200);
  delay(200);
  // calibrate current-sensor zero with the motor stopped
  float s = 0; for (uint8_t i = 0; i < 64; i++) { s += readVolts(PIN_ISENSE); delay(2); }
  acsZeroV = s / 64.0;
  // refuse to arm if a button is stuck / held at power-up
  if (digitalRead(PIN_BTN_IN) == LOW || digitalRead(PIN_BTN_OUT) == LOW) fault("button held at power-up");
  tone(PIN_BUZZER, 1500, 100);
}

void loop() {
  bool in  = pressed(PIN_BTN_IN);
  bool out = pressed(PIN_BTN_OUT);
  bool limitHit = digitalRead(PIN_LIMIT) == HIGH;
  uint32_t now = millis();

  // ---- FAULT: latch until both buttons released, then wait for a fresh press
  if (state == FAULT) {
    digitalWrite(PIN_LED, (now / 150) % 2);           // fast blink
    static uint32_t releasedAt = 0;
    if (!in && !out) { if (!releasedAt) releasedAt = now; if (now - releasedAt > 2000) { state = IDLE; releasedAt = 0; } }
    else releasedAt = 0;
    return;
  }

  // ---- both pressed = operator confusion -> stop
  if (in && out) { stopMotor(); return; }

  int8_t want = in ? 1 : (out ? -1 : 0);

  if (want == 0) {                                    // hold-to-run: released -> stop
    if (state != IDLE) stopMotor();
    digitalWrite(PIN_LED, limitHit ? (now / 500) % 2 : HIGH);   // slow blink = rope fully in
    return;
  }

  if (state == IDLE) {
    if (want == 1 && limitHit) { tone(PIN_BUZZER, 800, 80); return; }        // already fully wound in
    if (battVolts() < VBATT_MIN) { fault("battery low - charge it"); return; }
    if (want != lastDir && now - stoppedAt < REVERSE_DWELL_MS) return;       // let it stop first
    state = (want == 1) ? RUN_IN : RUN_OUT;
    lastDir = want; runStart = now; overSince = 0;
    setMotor(want, 0);
  }

  // ---- running
  uint8_t pwmMax = (state == RUN_IN) ? PWM_MAX_IN : PWM_MAX_OUT;
  uint32_t t = now - runStart;
  uint8_t target = (t >= RAMP_MS) ? pwmMax : (uint8_t)((uint32_t)pwmMax * t / RAMP_MS);
  setMotor(lastDir, target);
  tone(PIN_BUZZER, 1000);                              // continuous warning tone while moving
  digitalWrite(PIN_LED, HIGH);

  if (state == RUN_IN && limitHit) { stopMotor(); tone(PIN_BUZZER, 600, 400); return; }

  if (t > RAMP_MS) {                                   // ignore inrush during soft start
    if (motorAmps() > TRIP_AMPS) { if (!overSince) overSince = now; if (now - overSince > TRIP_MS) { fault("overload - tarp snagged?"); return; } }
    else overSince = 0;
  }
  if (t > MAX_RUN_MS) { fault("run time exceeded"); return; }

  static uint32_t lastLog = 0;
  if (now - lastLog > 500) {
    lastLog = now;
    Serial.print(state == RUN_IN ? F("IN ") : F("OUT ")); Serial.print(motorAmps(), 1);
    Serial.print(F(" A  ")); Serial.print(battVolts(), 1); Serial.println(F(" V"));
  }
}
