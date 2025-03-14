<!-- Manages all experiment interactions with the user, including
loading experiment data, showing the consent and video, and actually 
doing the experiment, with practice trials if necessary. 
It also shows the end survey at the end and uploads the experiment data
via the API.
 -->
<template>
  <div id="experiment" class="container">
    <!-- Manages notifications if allowed in the experiment -->
    <notifications
      group="alerts"
      position="top center"
      :max="2"
      :duration="6000"
      :width="450"
    ></notifications>
    <h1 class="text-center">
      Experiment "{{ experiment.name }}"<span class="text-success">{{
        practicing ? ": Practicing" : ""
      }}</span>
    </h1>
    <!-- Preparation Screen: video and consent form -->
    <prepscreen
      v-if="!preparation_screen_ready"
      v-bind="getPrepScreenObj"
      @prep-screen-ready="preparation_screen_ready = true"
    ></prepscreen>
    <!-- Preparation screen ready -->
    <template v-else>
      <div
        v-if="!experiment_started && !practicing && !experiment_finished"
        class="row"
      >
        <div class="col text-center">
          <!-- Practice trial instructions (if enabled in experiment) -->
          <template
            v-if="
              experiment.with_practice_trials && remaining_practice_trials > 0
            "
          >
            <p class="h4">
              Enter the sequence of characters in order when it appears on the
              screen
            </p>
            <p class="h4">Try to do it as fast and correctly as you can</p>
            <p class="h4">
              You will complete {{ remaining_practice_trials }} practice
              trial(s)
            </p>
            <p class="h4">
              Click on "Start Practice" when you're ready to begin practicing
            </p>
            <button class="btn btn-primary" @click="startPractice">
              Start Practice
            </button>
          </template>
          <!-- Experiment instructions -->
          <template v-else>
            <p class="h4" style="white-space: pre-wrap">
              {{ experiment.instructions }}
            </p>
            <!-- <p class="h4">
              Enter the sequence of characters in order when it appears on the
              screen
            </p>
            <p class="h4">Try to do it as fast and correctly as you can</p>
            <p class="h4 text-danger">
              Do not change window or tab, or the experiment will restart
            </p>
            <p class="h4">
              You will complete {{ blocks.length }} block(s) of trials
            </p>
            <p class="h4" v-if="isTypeNumTrials">
              On each block, you will have to do
              {{ blocks[current_block].num_trials }} trials
            </p>
            <p class="h4" v-else>
              On each block, you will have around
              {{ blocks[current_block].max_time }} seconds to do as many trials
              as you can
            </p>
            <p class="h4">
              You will start the experiment with your
              <span class="text-danger">{{ blocks[0].hand_to_use }}</span>
              hand. Between blocks you will be instructed on what hand to use
              for the next one.
            </p>
            <p class="h4">Make sure you only use one finger for each key</p>
            <p class="h4">
              After clicking on "Start Experiment", and before each block, you
              MAY hear an auditory cue
            </p>
            <p class="h4">
              Click on "Start Experiment" when you're ready to begin
            </p> -->
            <br />
            <button class="btn btn-primary btn-lg" @click="startExperiment">
              Start Experiment
            </button>
          </template>
        </div>
      </div>
      <!-- Practice trials -->
      <template v-else-if="practicing">
        <template v-if="rested_after_practice">
          <p class="text-success text-center">
            {{ remaining_practice_trials }} practice trials remaining
          </p>
          <div class="col-md-12 text-center">
            <button class="btn btn-primary text-center" @click="stopPractice">
              Stop Practice
            </button>
          </div>
          <p class="text-center">Enter the keys in order when they appear.</p>
          <trial
            ref="practice-trial"
            :practice="true"
            :random_seq="false"
            :sequence="experiment.practice_seq"
            :max_time_per_trial="experiment.practice_trial_time"
            :resting_time="experiment.practice_rest_time"
            :capturing_keypresses="true"
            :with_feedback="experiment.with_feedback"
            @trial-ended="practiceTrialEnded"
          ></trial>
        </template>
        <!-- Manage practice resting -->
        <div v-else class="text-center h5">
          Experiment appearing in:
          <countdown
            ref="timerAfterPractice"
            :time="experiment.rest_after_practice * 1000"
            :interval="100"
            :auto-start="true"
            :emit-events="true"
            @end="
              rested_after_practice = true;
              practicing = false;
            "
          >
            <span slot-scope="props">{{ props.seconds + 1 }}</span>
          </countdown>
        </div>
      </template>
      <!-- Actual Experiment -->
      <template v-else-if="experiment_started && !experiment_finished">
        <h4>Experiment Progress</h4>
        <!-- Show experiment progress (current block and how many are left) -->
        <b-progress height="2rem" :max="blocks.length" show-progress>
          <b-progress-bar
            :value="current_block + 1"
            :label="
              'Block ' +
              (current_block + 1).toString() +
              ' of ' +
              blocks.length.toString()
            "
          ></b-progress-bar>
        </b-progress>
        <br />
        <!-- Show block type (number of trials or max time) -->
        <p v-if="experiment.with_shown_instructions" class="text-center h3">
          Instructions:
          {{
            isTypeNumTrials
              ? "You will need to complete " +
                blocks[current_block].num_trials +
                " trials in this block."
              : "You will have " +
                blocks[current_block].max_time +
                " seconds on this block, and should try to do as many trials as possible."
          }}
        </p>
        <!-- Block countdown (just before starting a block)-->
        <div v-if="!block_started" class="text-center h2">
          Block starting in:
          <countdown
            ref="timerBlock"
            :time="
              blocks[current_block - 1]
                ? blocks[current_block - 1].sec_until_next * 1000
                : 3099
            "
            :interval="100"
            :auto-start="true"
            :emit-events="true"
            @progress="playCountdown"
            @end="startBlock"
          >
            <span slot-scope="props" class="h1">{{ props.seconds + 1 }}</span>
          </countdown>
          <!-- Show sequence to type -->
          <p class="text-center h4">
            Sequence:
            <span class="text-center h1">{{
              blocks[current_block].sequence
            }}</span>
          </p>
          <p class="text-center h4">
            Hand to use:
            <span class="text-center h1 text-primary">{{
              blocks[current_block].hand_to_use.charAt(0).toUpperCase() +
              blocks[current_block].hand_to_use.slice(1)
            }}</span>
          </p>
        </div>
        <!-- Block started-->
        <template v-else>
          <h4>Block Progress</h4>
          <!-- Show number of trials left if block is of that type -->
          <b-progress
            v-if="isTypeNumTrials"
            height="2rem"
            :max="blocks[current_block].num_trials"
            show-progress
          >
            <b-progress-bar
              :value="current_trial + 1"
              :label="
                'Trial ' +
                (current_trial + 1).toString() +
                ' of ' +
                blocks[current_block].num_trials.toString()
              "
            ></b-progress-bar>
          </b-progress>
          <!-- Show the number of seconds left if block is of that type -->
          <div v-else>
            <countdown
              ref="timerBlock"
              :time="blocks[current_block].max_time * 1000"
              :interval="1000"
              :auto-start="true"
              @progress="blockTimerProgress"
              @end="blockEnded(true)"
            >
            </countdown>
            <b-progress
              height="2rem"
              :max="blocks[current_block].max_time"
              show-progress
            >
              <!-- Show status of countdown timer -->
              <b-progress-bar
                :value="current_block_time"
                :label="
                  current_block_time.toString() +
                  ' seconds of ' +
                  blocks[current_block].max_time.toString()
                "
              ></b-progress-bar>
            </b-progress>
          </div>
          <br />
          <!-- Trial: receives keypresses and manages appropriately painting the sequence squares -->
          <trial
            ref="real-trial"
            v-bind="getTrialObj"
            @trial-ended="trialEnded"
            @rest-ended="restEnded"
          >
          </trial>
          <!-- If experiment should show feedback of performance in each block -->
          <template v-if="experiment.with_feedback_blocks">
            <h4>Block performance</h4>
            <b-progress
              height="2rem"
              :max="num_correct_seq + num_incorrect_seq"
              show-progress
            >
              <b-progress-bar
                :value="num_correct_seq"
                :label="num_correct_seq.toString() + ' correct'"
                variant="success"
              ></b-progress-bar>
              <b-progress-bar
                :value="num_incorrect_seq"
                :label="num_incorrect_seq.toString() + ' incorrect'"
                variant="danger"
              ></b-progress-bar>
            </b-progress>
          </template>
        </template>
      </template>
      <!-- End Survey -->
      <div v-if="experiment_finished">
        <h3 class="text-center">Tell us something about you</h3>
        <!-- Manual sending of data if automatic failed -->
        <template
          v-if="!correctly_sent_data && unsuccessful_data_sent_counter > 0"
        >
          <div>
            <p class="text-danger">
              Data could not be sent to the server. Please connect to the
              internet and then click on the button below
            </p>
            <b-button
              class="btn"
              variant="primary"
              @click="$emit('send-data', experiment_blocks)"
              >Send Data</b-button
            >
          </div>
        </template>
        <br />
        <!-- Survey form -->
        <b-form @submit="leaveExperiment">
          <!-- Redirect home when done -->
          <div class="form-row">
            <b-form-group class="col-4" label="Age:" label-for="age">
              <b-form-input
                name="age"
                id="age"
                v-model="questionnaire.age"
                type="number"
                required
                placeholder="Age"
              ></b-form-input>
            </b-form-group>
            <b-form-group class="col-4" label="Gender:" label-for="gender">
              <b-form-select
                id="gender"
                v-model="questionnaire.gender"
                :options="gender_opts"
                required
              ></b-form-select>
            </b-form-group>
            <b-form-group
              class="col-4"
              label="Computer type:"
              label-for="comp-type"
            >
              <b-form-select
                id="comp-type"
                v-model="questionnaire.comp_type"
                :options="comp_type_opts"
                required
              ></b-form-select>
            </b-form-group>
          </div>
          <div class="form-row">
            <b-form-group
              class="col"
              label="Do you have any medical conditions (e.g., recent surgery, fracture, vision problem, stroke) that could have potentially affected your performance on the task?"
            >
              <b-form-radio-group
                id="medcondition-radio"
                v-model="questionnaire.medical_condition"
                name="medcondition-radio"
                required
              >
                <b-form-radio :value="true">Yes</b-form-radio>
                <b-form-radio :value="false">No</b-form-radio>
              </b-form-radio-group>
            </b-form-group>
          </div>
          <div class="form-row">
            <b-form-group class="col-4" label="Do you exercise regularly?">
              <b-form-radio-group
                id="exercise-radio"
                v-model="questionnaire.excercise_regularly"
                name="exercise-radio"
                required
              >
                <b-form-radio :value="true">Yes</b-form-radio>
                <b-form-radio :value="false">No</b-form-radio>
              </b-form-radio-group>
            </b-form-group>
            <b-form-group
              class="col-4"
              label="Maximum level of education:"
              label-for="level-education"
            >
              <b-form-select
                id="level-education"
                v-model="questionnaire.level_education"
                :options="level_education_opts"
                required
              ></b-form-select>
            </b-form-group>
          </div>
          <div class="form-row">
            <b-form-group
              class="col-4"
              label="How many hours did you sleep yesterday?"
              label-for="age"
            >
              <b-form-input
                name="sleep"
                id="sleep"
                v-model="questionnaire.hours_of_sleep"
                type="number"
                required
                placeholder="Hours of sleep"
              ></b-form-input>
            </b-form-group>
            <b-form-group
              class="col-4"
              label="Have you done a similar keypressing experiment before?"
            >
              <b-form-radio-group
                id="similar-exp-radio"
                v-model="questionnaire.keypress_experiment_before"
                name="similar-exp-radio"
                required
              >
                <b-form-radio :value="true">Yes</b-form-radio>
                <b-form-radio :value="false">No</b-form-radio>
              </b-form-radio-group>
            </b-form-group>
            <b-form-group
              class="col-4"
              label="Did you follow the experiment instructions?"
            >
              <b-form-radio-group
                id="followed-instructions"
                v-model="questionnaire.followed_instructions"
                name="followed-instructions"
                required
              >
                <b-form-radio :value="true">Yes</b-form-radio>
                <b-form-radio :value="false">No</b-form-radio>
              </b-form-radio-group>
            </b-form-group>
          </div>
          <div class="form-row">
            <b-form-group
              class="col-4"
              label="Dominant hand:"
              label-for="dominant-hand"
            >
              <b-form-select
                id="dominant-hand"
                v-model="questionnaire.dominant_hand"
                :options="hand_used_opts"
                required
              ></b-form-select>
            </b-form-group>
            <b-form-group
              class="col-4"
              label="Hand used for experiments:"
              label-for="hand-used"
            >
              <b-form-select
                id="hand-used"
                v-model="questionnaire.hand_used"
                :options="hand_used_opts"
                required
              ></b-form-select>
            </b-form-group>
          </div>
          <div class="form-row">
            <b-form-group
              label="Do you have any comments on your experience and what could be improved?"
              label-for="comments"
              class="col-6"
            >
              <b-form-textarea
                id="comments"
                v-model="questionnaire.comment"
                placeholder="Enter your comments"
                rows="3"
                max-rows="6"
              ></b-form-textarea>
            </b-form-group>
          </div>
          <!-- Submit button -->
          <b-button
            type="submit"
            class="btn btn-block"
            :disabled="!correctly_sent_data"
            variant="primary"
            >Submit and exit</b-button
          >
        </b-form>
      </div>
    </template>
  </div>
</template>

<script>
module.exports = {
  data: function () {
    return {
      preparation_screen_ready: false,
      practicing: false,
      practice_finished: false,
      remaining_practice_trials: 0,
      rested_after_practice: true,

      experiment_started: false,
      experiment_finished: false,
      block_started: false,
      current_block: 0,
      current_block_time: 0,
      current_trial: 0,
      num_correct_seq: 0,
      num_incorrect_seq: 0,
      resting: false,
      capturing_keypresses: false,
      current_inputted_sequence: [],

      started_trial_at: null,
      keypresses_trial: [],
      block_trials: [],
      experiment_blocks: [],

      played_countdown: false,

      // For the end survey
      questionnaire: {
        age: null,
        gender: null,
        comp_type: null,
        comment: null,
        medical_condition: null,
        hours_of_sleep: null,
        excercise_regularly: null,
        keypress_experiment_before: null,
        followed_instructions: null,
        hand_used: null,
        dominant_hand: null,
        level_education: null,
      },
      // Options for survey
      gender_opts: { male: "Male", female: "Female", other: "Other" },
      comp_type_opts: { laptop: "Laptop", desktop: "Desktop", other: "Other" },
      hand_used_opts: { left: "Left", right: "Right", both: "Both" },
      level_education_opts: {
        kindergarten_or_below: "Kindergarten and below",
        first_to_sixth: "1st to 6th grade",
        seventh_to_ninth: "7th to 9th grade",
        tenth_to_twelfth: "10th to 12th grade",
        community_college_or_associate_degree:
          "Community college or associate degree",
        bachelor: "Bachelor's degree",
        master_or_phd: "Master's or doctoral degree",
      },

      countdown_audio: new Audio("/static/gestureApp/sound/countdown.wav"),

      // Extract video and consent files from public URLs in Cloud Storage
      video_url: `https://storage.googleapis.com/motor-learning/experiment_files/${this.experiment.code}/video.mp4`,
      pdf_url: `https://storage.googleapis.com/motor-learning/experiment_files/${this.experiment.code}/consent.pdf`,
    };
  },
  props: {
    experiment: Object,
    blocks: Array,
    // Whether the data was correctly sent to the API or not
    correctly_sent_data: Boolean,
    // Number of tries
    unsuccessful_data_sent_counter: Number,
    subject_code: String,
  },
  mounted: function () {
    // window.addEventListener('keydown', this.keydownHandler);
    this.remaining_practice_trials = this.experiment.num_practice_trials;
    // Handle page visibility change events
    function visibilityListener() {
      switch (document.visibilityState) {
        case "hidden":
          window.location.reload();
          break;
        case "visible":
          console.log("visible");
          break;
      }
    }
    // Reload page when user changes tabs, so that the experiment data does not get affected
    document.addEventListener("visibilitychange", visibilityListener);
  },
  components: {
    trial: httpVueLoader("/static/gestureApp/js/components/Trial.vue"),
    prepscreen: httpVueLoader(
      "/static/gestureApp/js/components/PreparationScreen.vue"
    ),
  },
  computed: {
    getTrialObj() {
      // Passes the trial info directly to the trial component
      return {
        sequence: this.blocks[this.current_block].sequence,
        resting: this.resting,
        max_time_per_trial: this.blocks[this.current_block].max_time_per_trial,
        resting_time: this.blocks[this.current_block].resting_time,
        capturing_keypresses: this.capturing_keypresses,
        with_feedback: this.experiment.with_feedback,
      };
    },
    isTypeNumTrials() {
      // Returns whether the block is of type num trials or not
      if (this.blocks[this.current_block].type === "num_trials") return true;
      return false;
    },
    getPrepScreenObj() {
      // Passes all the necessary objects to the prep screen component
      return {
        exp_code: this.experiment.code,
        video_url: this.video_url,
        pdf_url: this.pdf_url,
        requirements: this.experiment.requirements,
      };
    },
  },
  methods: {
    startExperiment: function () {
      this.experiment_started = true;
      var elem = document.documentElement;
      // Switches to full screen, depending on the browser
      if (elem.requestFullscreen) {
        elem.requestFullscreen();
      } else if (elem.webkitRequestFullscreen) {
        /* Safari */
        elem.webkitRequestFullscreen();
      } else if (elem.msRequestFullscreen) {
        /* IE11 */
        elem.msRequestFullscreen();
      }
    },
    startPractice() {
      this.practicing = true;
      var elem = document.documentElement;
      // Switches to full screen, depending on the browser
      if (elem.requestFullscreen) {
        elem.requestFullscreen();
      } else if (elem.webkitRequestFullscreen) {
        /* Safari */
        elem.webkitRequestFullscreen();
      } else if (elem.msRequestFullscreen) {
        /* IE11 */
        elem.msRequestFullscreen();
      }
    },
    stopPractice() {
      // Stops practice and starts rest
      this.$refs["practice-trial"].stopPractice();
      this.rested_after_practice = false;
    },
    startBlock: function () {
      this.played_countdown = false;
      this.block_started = true;
      this.capturing_keypresses = true;
      this.current_block_time = 0;
      this.startTrial();
    },
    startTrial: function () {
      this.started_trial_at = new Date().getTime();
    },
    practiceTrialEnded(
      correct,
      keypresses_trial,
      inputted_sequence,
      sequence,
      partial_correct
    ) {
      // Runs when a practice trial ended. It either starts the next trial or stops the practice.
      if (this.experiment.with_feedback) {
        if (correct) {
          this.$notify({
            group: "alerts",
            title: "Correct input sequence",
            type: "success",
          });
        } else {
          this.$notify({
            group: "alerts",
            title: "Error in input sequence",
            // text: `
            //       Target sequence was '${sequence}', and your input was '${inputted_sequence.join(
            //   ""
            // )}'
            //       `,
            type: `error`,
          });
        }
      }
      this.remaining_practice_trials--;
      if (this.remaining_practice_trials <= 0) this.stopPractice();
    },
    trialEnded: function (
      correct,
      keypresses_trial,
      inputted_sequence,
      sequence,
      partial_correct
    ) {
      if (correct) {
        if (this.experiment.with_feedback) {
          this.$notify({
            group: "alerts",
            title: "Correct input sequence",
            type: "success",
          });
        }
        this.num_correct_seq++;
      } else {
        if (this.experiment.with_feedback) {
          this.$notify({
            group: "alerts",
            title: "Error in input sequence",
            text: `
                    Target sequence was '${sequence}', and your input was '${inputted_sequence.join(
              ""
            )}'
                    `,
            type: `error`,
          });
        }
        this.num_incorrect_seq++;
      }
      let finished_at = new Date().getTime();
      this.block_trials.push({
        started_at: this.started_trial_at,
        keypresses: keypresses_trial,
        correct: correct,
        partial_correct: partial_correct,
        finished_at: finished_at,
      });
      this.started_trial_at = null;
    },
    restEnded: function () {
      //   Go to the next trial if there is one
      if (
        !this.isTypeNumTrials ||
        (this.isTypeNumTrials &&
          this.current_trial + 1 < this.blocks[this.current_block].num_trials)
      ) {
        this.current_trial++;
        this.startTrial();
      }
      // Check if there are any blocks left
      else this.blockEnded();
    },
    blockEnded: function (from_timer = false) {
      // If the block ended from timer, force the trial ending too
      if (from_timer) {
        this.$refs["real-trial"].trialEnded(true, true, this.started_trial_at);
      }
      this.experiment_blocks.push(this.block_trials);
      this.block_trials = new Array();
      this.current_trial = 0;
      this.num_correct_seq = 0;
      this.num_incorrect_seq = 0;
      this.block_started = false;
      this.capturing_keypresses = false;

      if (this.current_block + 1 >= this.blocks.length) this.experimentEnded();
      else this.current_block++;
    },
    experimentEnded: function () {
      this.block_trials = new Array();
      this.current_block = 0;
      this.current_trial = 0;
      this.num_correct_seq = 0;
      this.num_incorrect_seq = 0;
      this.block_started = false;
      this.capturing_keypresses = false;

      this.experiment_finished = true;

      // To send the data automatically
      this.$emit("send-data", this.experiment_blocks);
    },
    blockTimerProgress(data) {
      this.current_block_time = Math.floor(
        this.blocks[this.current_block].max_time -
          (data.hours * 3600 +
            data.minutes * 60 +
            data.seconds +
            0.001 * data.milliseconds)
      );
    },
    leaveExperiment(evt) {
      evt.preventDefault();
      this.$emit("end-survey", this.questionnaire);
    },
    playCountdown(data) {
      // Play countdown sound when almost three seconds are left. Won't be exactly 3.
      var remaining = data.seconds + data.milliseconds / 1000.0;
      
      // Check if we have enough time between blocks to play the countdown
      let hasEnoughTimeBetweenBlocks = true;
      if (this.current_block > 0) {
        hasEnoughTimeBetweenBlocks = this.blocks[this.current_block - 1].sec_until_next >= 3;
      }
      
      // Only play countdown if there's enough time and we haven't played it yet
      if (remaining <= 3.15 && !this.played_countdown && hasEnoughTimeBetweenBlocks) {
        this.countdown_audio.play();
        this.played_countdown = true;
      }
    },
  },
};
</script>

<style scoped>
.seq-charact {
  border: 1px solid black;
  display: inline-block;
  width: 100px;
  padding: 40px 0;
  background-color: lightgray;
  text-align: center;
  font-size: 40px;
}
h2 {
  text-align: center;
}
.top-buffer {
  margin-top: 10px;
}
/* .my-notification.success {
  background: #85c0f9;
  border-left-color: #85c1f9bd;
}

.my-notification.warn {
  background: #ffb648;
  border-left-color: #f48a06;
}

.my-notification.error {
  background: #f5793a;
  border-left-color: #f5783abe;
} */
</style>
