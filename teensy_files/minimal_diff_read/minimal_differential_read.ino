#include <ADC.h>        // ADC library from https://github.com/pedvide/ADC

ADC *adc = new ADC();

volatile int16_t val;

void setup() {
        pinMode(LED_BUILTIN, OUTPUT);
        Serial.begin(115200);                       // opens serial port, sets data rate to 115200 bps
        delay(1000);                                // wait 1 second
        adc->adc0->enablePGA(16);                   // enables the programmable-gain amplifier, can be 1, 2, 4, 8, 16, 32 or 64
        adc->adc0->setResolution(16);               // use all 16 bits of ADC resolution. In Differential mode, is 15 bits + sign bit
        adc->adc0->setAveraging(32);                // use hardware averaging, can be 0, 4, 8, 16 or 32
}

void loop() {
        digitalWriteFast(LED_BUILTIN, !digitalReadFast(LED_BUILTIN));   // toggle LED
        val = adc->adc0->analogReadDifferential(A10,A11);               // do differential read
        Serial.println(val);                                            // print result to serial
        delay(10);                                                      // wait 10 ms
}
