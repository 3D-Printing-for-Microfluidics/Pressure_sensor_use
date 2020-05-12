/* Trigger both ADCs with Timer
    Example usage:
        Start the timers at some period (us): s 3000<cr>
        print out the current period: p<cr>
        Stop the timers: s<cr>
*/

#include <ADC.h>
#include <ADC_util.h>

#define BAUD_RATE 115200

volatile int timer_period_us;

IntervalTimer timer0;

elapsedMillis ms_since_start;

ADC *adc = new ADC(); // adc object;

double V_per_bit_adc0;
double V_per_bit_adc1;

void setup() {

    // serial IO setup
    Serial.begin(BAUD_RATE);
    while (!Serial && millis() < 5000) ;    // wait up to 5 seconds for serial comms to start

    // pin configuration  
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(A10, INPUT);            // adc0 differential positive pin
    pinMode(A11, INPUT);            // adc0 differential negative pin
    pinMode(A12, INPUT);            // adc1 differential positive pin
    pinMode(A13, INPUT);            // adc1 differential negative pin

    // ADC0 setup
    adc->adc0->setAveraging(32);                                            // set number of averages. Can be 0, 4, 8, 16 or 32
    adc->adc0->setResolution(16);                                           // set bits of resolution. For differential measurements: 9, 11, 13 or 16 bits
    adc->adc0->setConversionSpeed(ADC_CONVERSION_SPEED::MED_SPEED);         // change the conversion speed. Can be VERY_LOW_SPEED, LOW_SPEED, MED_SPEED, HIGH_SPEED or VERY_HIGH_SPEED
    adc->adc0->setSamplingSpeed(ADC_SAMPLING_SPEED::MED_SPEED);             // change the sampling speed. Can be VERY_LOW_SPEED, LOW_SPEED, MED_SPEED, HIGH_SPEED or VERY_HIGH_SPEED
    adc->adc0->enablePGA(16);                                               // enables PGA (programmable gain amplifier) and sets gain. Can be 1, 2, 4, 8, 16, 32 or 64

    // ADC1 setup
    adc->adc1->setAveraging(32);                                            // set number of averages. Can be 0, 4, 8, 16 or 32
    adc->adc1->setResolution(16);                                           // set bits of resolution. For differential measurements: 9, 11, 13 or 16 bits
    adc->adc1->setConversionSpeed(ADC_CONVERSION_SPEED::MED_SPEED);         // change the conversion speed. Can be VERY_LOW_SPEED, LOW_SPEED, MED_SPEED, HIGH_SPEED or VERY_HIGH_SPEED
    adc->adc1->setSamplingSpeed(ADC_SAMPLING_SPEED::MED_SPEED);             // change the sampling speed. Can be VERY_LOW_SPEED, LOW_SPEED, MED_SPEED, HIGH_SPEED or VERY_HIGH_SPEED
    adc->adc1->enablePGA(16);                                               // enables PGA (programmable gain amplifier) and sets gain. Can be 1, 2, 4, 8, 16, 32 or 64

    // divide by the maximum possible value and the PGA level
    V_per_bit_adc0 = 3.3/adc->adc0->getPGA()/adc->adc0->getMaxValue();
    V_per_bit_adc1 = 3.3/adc->adc1->getPGA()/adc->adc1->getMaxValue();

}

char c = 0;
void loop() {
    if (Serial.available()) {
        c = Serial.read();
        if (c == 's') {     // set timer period. Set to 0 to disable
            timer_period_us = Serial.parseInt();
            if (timer_period_us == 0) {
                timer0.end();
                digitalWriteFast(LED_BUILTIN, 0);
            }
            else {
                timer0.begin(timer0_isr, timer_period_us);
            }
        } else if (c == 'p') { // query timer period
            Serial.println(timer_period_us, DEC);
        }
    }

    // print errors, if any
    if (adc->adc0->fail_flag != ADC_ERROR::CLEAR) {
        Serial.print("ADC0 error: ");
        Serial.println(getStringADCError(adc->adc0->fail_flag));
    }
    if (adc->adc1->fail_flag != ADC_ERROR::CLEAR) {
        Serial.print("ADC1 error: ");
        Serial.println(getStringADCError(adc->adc1->fail_flag));
    }
    adc->resetError();
    delay(10);  // wait 10 ms before checking for more input and checking error state
}

void timer0_isr() {
    // do reads
    int16_t adc0_diff_value = adc->adc0->analogReadDifferential(A10, A11);
    int16_t adc1_diff_value = adc->adc1->analogReadDifferential(A12, A13);

    // send data over serial
    Serial.print(ms_since_start, DEC);
    Serial.print(":");
    Serial.print(adc0_diff_value, DEC);
    Serial.print(":");
    Serial.println(adc1_diff_value, DEC);

    // toggle LED every time isr fires
    digitalWriteFast(LED_BUILTIN, !digitalReadFast(LED_BUILTIN));
}
