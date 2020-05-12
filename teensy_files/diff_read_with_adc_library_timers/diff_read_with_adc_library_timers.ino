/* Example for triggering the ADC with Timer

    *** NOT FUNCTIONAL (included here for future development. The adc vaalues aren't correct, but the timers do fire as expected)

    Example usage:
        Start the timers at some frequency: s 3000<cr>
        get a single read from the ADC(s): v<cr>
        print out the actual frequency: p<cr>
        Read in a whole buffer and print out data: t<cr>
        Stop the timers: s<cr>
*/


#include <ADC.h>        // ADC library from https://github.com/pedvide/ADC
#include <ADC_util.h>

const int readPin = A10; // ADC0
const int readPin2 = A12; // ADC1

ADC *adc = new ADC(); // adc object;

#define BAUD_RATE 115200  //921600 //460800 // 230400 //115200
#define BUFFER_SIZE 500

uint16_t buffer_ADC_0[BUFFER_SIZE];
uint16_t buffer_adc_0_count = 0xffff;
uint32_t delta_time_adc_0 = 0;
uint16_t buffer_ADC_1[BUFFER_SIZE];
uint16_t buffer_adc_1_count = 0xffff;
uint32_t delta_time_adc_1 = 0;

elapsedMillis timed_read_elapsed;

double V_per_bit;

void setup() {

    Serial.begin(BAUD_RATE);
    Serial.println("Begin setup");
    while (!Serial && millis() < 5000) ; // wait up to 5 seconds for serial comms to start


    pinMode(LED_BUILTIN, OUTPUT);

    pinMode(A10, INPUT); //Diff Positive ADC_0
    pinMode(A11, INPUT); //Diff Negative ADC_0

    pinMode(A12, INPUT); //Diff Positive ADC_1
    pinMode(A13, INPUT); //Diff Negative ADC_1

    ///// ADC0 ////
    adc->adc0->setAveraging(16); // set number of averages
    adc->adc0->setResolution(16); // set bits of resolution

    // it can be any of the ADC_CONVERSION_SPEED enum: VERY_LOW_SPEED, LOW_SPEED, MED_SPEED, HIGH_SPEED_16BITS, HIGH_SPEED or VERY_HIGH_SPEED
    // see the documentation for more information
    adc->adc0->setConversionSpeed(ADC_CONVERSION_SPEED::MED_SPEED); // change the conversion speed
    // it can be any of the ADC_MED_SPEED enum: VERY_LOW_SPEED, LOW_SPEED, MED_SPEED, HIGH_SPEED or VERY_HIGH_SPEED
    adc->adc0->setSamplingSpeed(ADC_SAMPLING_SPEED::MED_SPEED); // change the sampling speed

    // Enable and set PGA
    /** void enablePGA(uint8_t gain);
    *   Enables the PGA and sets the gain
    *   Use only for signals lower than 1.2 V and only in differential mode
    *   param gain can be 1, 2, 4, 8, 16, 32 or 64
    */
    adc->adc0->enablePGA(8);

    // always call the compare functions after changing the resolution!
    //adc->enableCompare(1.0/3.3*adc->getMaxValue(ADC_0), 0, ADC_0); // measurement will be ready if value < 1.0V
    //adc->enableCompareRange(1.0*adc->getMaxValue(ADC_0)/3.3, 2.0*adc->getMaxValue(ADC_0)/3.3, 0, 1, ADC_0); // ready if value lies out of [1.0,2.0] V

    // If you enable interrupts, notice that the isr will read the result, so that isComplete() will return false (most of the time)
    //adc->enableInterrupts(adc0_isr, ADC_0);


    ////// ADC1 /////
    adc->adc1->setAveraging(16); // set number of averages
    adc->adc1->setResolution(16); // set bits of resolution
    adc->adc1->setConversionSpeed(ADC_CONVERSION_SPEED::MED_SPEED); // change the conversion speed
    adc->adc1->setSamplingSpeed(ADC_SAMPLING_SPEED::MED_SPEED); // change the sampling speed
    adc->adc1->enablePGA(8);

    // divide by the maximum possible value and the PGA level
    V_per_bit = 3.3/adc->adc0->getPGA()/adc->adc0->getMaxValue();

    Serial.println("End setup");

    Serial.println("Enter a command such as: s 3000<cr> to start doing something");

}

char c = 0;
int value;
int value2;

void loop() {

  if (Serial.available()) {
    c = Serial.read();
    if (c == 'v') { // value
      Serial.print("Value ADC0: ");
      value = (uint16_t)adc->adc0->readSingle(); // the unsigned is necessary for 16 bits, otherwise values larger than 3.3/2 V are negative!
      Serial.printf("%d = ", value);
      Serial.println(value * 3.3 / adc->adc0->getMaxValue(), DEC);
      Serial.print("Value ADC1: ");
      value2 = (uint16_t)adc->adc1->readSingle(); // the unsigned is necessary for 16 bits, otherwise values larger than 3.3/2 V are negative!
      Serial.printf("%d = ", value2);
      Serial.println(value2 * 3.3 / adc->adc1->getMaxValue(), DEC);
    } else if (c == 's') { // start Timer, before pressing enter write the frequency in Hz
      uint32_t freq = Serial.parseInt();
      if (freq == 0) {
        Serial.println("Stop Timer.");
        adc->adc0->stopTimer();
        adc->adc1->stopTimer();
      }
      else {
        Serial.print("Start Timer with frequency ");
        Serial.print(freq);
        Serial.println(" Hz.");
        adc->adc0->stopTimer();
        adc->adc0->startSingleRead(readPin); // call this to setup everything before the Timer starts, differential is also possible
        adc->adc0->enableInterrupts(adc0_isr);
        adc->adc0->startTimer(freq); //frequency in Hz
        adc->adc1->stopTimer();
        adc->adc1->startSingleRead(readPin2); // call this to setup everything before the Timer starts
        adc->adc1->enableInterrupts(adc1_isr);
        adc->adc1->startTimer(freq); //frequency in Hz
      }
    } else if (c == 'p') { // print Timer stats
      Serial.print("Frequency: ");
      Serial.println(adc->adc0->getTimerFrequency());
    } else if (c == 't') { // Lets try a timed read
      timed_read_elapsed = 0;
      buffer_adc_0_count = 0;
      buffer_adc_1_count = 0;
      Serial.println("Starting Timed read");
    }
  }

  // Print errors, if any.
  if (adc->adc0->fail_flag != ADC_ERROR::CLEAR) Serial.print("ADC0: "); Serial.println(getStringADCError(adc->adc0->fail_flag));
  if (adc->adc1->fail_flag != ADC_ERROR::CLEAR) Serial.print("ADC1: "); Serial.println(getStringADCError(adc->adc1->fail_flag));
  adc->resetError();

  // See if we have a timed read test that finished.
  if (delta_time_adc_0) printTimedADCInfo(ADC_0, buffer_ADC_0, delta_time_adc_0);
  if (delta_time_adc_1) printTimedADCInfo(ADC_1, buffer_ADC_1, delta_time_adc_1);

  delay(10);
}

void printTimedADCInfo(uint8_t adc_num, uint16_t *buffer, uint32_t &delta_time) {
  uint32_t min_value = 0xffff;
  uint32_t max_value = 0;
  uint32_t sum = 0;
  for (int i = 0; i < BUFFER_SIZE; i++) {
    if (buffer[i] < min_value) min_value = buffer[i];
    if (buffer[i] > max_value) max_value = buffer[i];
    sum += buffer[i];
  }
  float average_value = (float)sum / BUFFER_SIZE; // get an average...
  float sum_delta_sq = 0;
  for (int i = 0; i < BUFFER_SIZE; i++) {
    int delta_from_center = (int)buffer[i] - average_value;
    sum_delta_sq += delta_from_center * delta_from_center;
  }
  int rms = sqrt(sum_delta_sq / BUFFER_SIZE);
  Serial.printf("ADC:%d delta time:%d freq:%d - min:%d max:%d avg:%d rms:%d\n", adc_num,
                delta_time, (1000 * BUFFER_SIZE) / delta_time,
                min_value, max_value, (int)average_value, rms);

  delta_time = 0;

}

void adc0_isr() {
    adc->adc0->readSingle();        // Make sure to call readSingle() to clear the interrupt.
    int diff_value = adc->adc0->analogReadDifferential(A10, A11); // read a new value, will return ADC_ERROR_VALUE if the comparison is false.
    Serial.print("A10-A11: ");
    Serial.println(diff_value);

    if (buffer_adc_0_count < BUFFER_SIZE) {
        buffer_ADC_0[buffer_adc_0_count++] = diff_value;
        if (buffer_adc_0_count == BUFFER_SIZE) delta_time_adc_0 = timed_read_elapsed;
    }
    digitalWriteFast(LED_BUILTIN, !digitalReadFast(LED_BUILTIN) );
}

void adc1_isr() {
    uint16_t adc_val = adc->adc1->readSingle();
    if (buffer_adc_1_count < BUFFER_SIZE) {
        buffer_ADC_1[buffer_adc_1_count++] = adc_val;
        if (buffer_adc_1_count == BUFFER_SIZE) delta_time_adc_1 = timed_read_elapsed;
    }
}
