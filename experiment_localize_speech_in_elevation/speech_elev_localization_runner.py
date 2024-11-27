import sys
sys.path.append('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/SpeakerArray/src')
from utils import speaker_utils
import numpy as np
import pickle
import asyncio
from scipy.io import wavfile
import sounddevice as sd
import pdb
import json
from pathlib import Path
import dataclasses
from typing import Any

##################
# INIT Global vars 
##################
DB_SPL = 65
DB_SPL_SPEAKER_WAKE = 40
BLOCK_LEN = 360 # 35 for v01 and old expmnts 28 for v00 relative dist exp. 

PART_IX = 3
EXP_DIR = Path("speaker_array_manifests")
PART_NAME = f"participant_{PART_IX:03d}"
EXP_TYPE = "localize_speech_in_elevation_v00"  # Name of sub directory to save experiment results - should match dir of trial dicts!

EXPMT_TRIAL_DICT_NAME = f"{EXP_TYPE}/{PART_NAME}_pilot_trial_dict.pkl"

# params that could but usually shouldn't change 
EXPMT_TRIAL_DICT_DIR = Path("/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_localize_speech_in_elevation/speaker_array_manifests")
EXPMT_TRIAL_DICT_PATH = EXPMT_TRIAL_DICT_DIR / EXPMT_TRIAL_DICT_NAME
SPEAKER_CONFIG = speaker_utils.create_speaker_config('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/SpeakerArray/assets/Layouts/NewSpeakerLayoutUpdate.csv')


OUTPUT_DIR = Path("/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/msjspsych-main/experiment_localize_speech_in_elevation/data")
OUTPUT_DIR = OUTPUT_DIR / EXP_TYPE
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE_NAME = OUTPUT_DIR / f'{PART_NAME}.json'


@dataclasses.dataclass
class Trial:
    trial_num: int
    locations: list[tuple]
    response: Any


def initialize_exp(speaker_config, break_sound_path, block_start_sound_path, manifest_path):
    dev = speaker_utils.set_DAC()
    print(f"{dev=}")
    if dev == "16A":
        asyncio.run(speaker_utils.force_unroute_all(speaker_config))

    break_sound, break_soundsr = wavfile.read(break_sound_path)
    block_start_sound, block_start_soundsr = wavfile.read(block_start_sound_path)
    break_sound = speaker_utils.set_dba_level(break_sound, DB_SPL)
    block_start_sound = speaker_utils.set_dba_level(block_start_sound, DB_SPL)

    # wait for message
    # run_exp(indx, trials, etc....)
    # wait for next message


async def zap_speakers(
    speaker_config: dict, duration: int
) -> None:
    """Plays whitenoise through all the speakersfor

    Args:
        speaker_config (dict): A dictionary containing the configuration of the speakers.
        noise_sr (int): The sample rate of the white noise.
        noise_dba (int): The decibel level of the white noise.
        duration (int): The duration of the white noise in seconds.

    Returns:
        None
    """
    await speaker_utils.force_route_all(0, speaker_config)
    noise = speaker_utils.whitenoise(duration, 44100, dba=DB_SPL_SPEAKER_WAKE)
    sd.play(noise, 44100, blocking=True)
    await speaker_utils.force_unroute_all(speaker_config)
    input("speakers ready. press enter to continue")


def save_trials(trials: list, save_path: Path):
    td = {i: t.__dict__ for i, t in enumerate(trials)}
    with open(save_path, "w") as f:
        json.dump(td, f, default=lambda x: str(x))


async def setup_trial(
    idx: int,
    speaker_config: dict,
    break_sound: np.ndarray,
    break_soundsr: int,
    block_start_sound: np.ndarray,
    block_start_soundsr: int,
    make_output_file: bool,
    responses: list,
    block_length=90,
):
    """
    Asynchronously sets up the trial with the given configuration and plays break sounds if required.

    Args:
        idx (int): Index of the current trial.
        exp_config (cfg.SemanticCueConfig): Configuration object for the experiment.
        speaker_config (dict): A dictionary containing the configuration of the speakers.
        break_sound (np.ndarray): An array of sound to be played during the break.
        break_soundsr (int): The sample rate of the break sound.
        make_output_file (bool): A boolean indicating whether to create an output file or not.
        responses (list[tu.SemanticCueTrial]): A list to store the trial responses.
        block_start_sound (np.ndarray): An array of sound to be played at the start of the block.
        block_start_soundsr (int): The sample rate of the block start sound.

    Returns:
        None

    Raises:
        N/A
    """

    if idx % block_length == 0:
        # import pdb; pdb.set_trace()
        await speaker_utils.force_unroute_all(speaker_config)
        if idx != 0:
            await speaker_utils.route_speaker_on((0, 0), 0, speaker_config)
            sd.play(break_sound, break_soundsr, blocking=True)
            while (
                input("Take a break, enter 'ready' to activate speakers: ").lower() != "ready"
            ):
                pass

        else:
            input("initializing speakers. press enter when ready")

        await zap_speakers(speaker_config, duration=5)


    # indicate a block switch
    # save trials on every block switch
    if block_length is not None and idx % block_length == 0:
        await speaker_utils.force_unroute_all(speaker_config)
        await speaker_utils.route_speaker_on((0, 0), 0, speaker_config)
        sd.play(block_start_sound, block_start_soundsr, blocking=False)
        if make_output_file:
            save_trials(responses, OUTPUT_FILE_NAME)
        sd.wait()
        await speaker_utils.unroute_speaker((0, 0), speaker_config)
        # wait for input after trial is set up


async def route_trial_speakers(
    trial: tuple, speaker_config: dict
) -> None:
    loc = [trial[0]]# is (azim, elev)
    print(f"routing {loc=}", end="| ")
    await speaker_utils.route_speakers(loc, np.arange(len(loc)), speaker_config)


def load_sounds(
    trial: tuple,
) -> np.ndarray:
    """
    Load audio files for a given semantic cue trial and return the trial sounds and stimulus silence.

    Args:
        trial (tu.SemanticControlTrial): The trial to load sounds for.
        exp_config (cfg.SemanticCueControlConfig): The experimental configuration.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing the trial sounds and stimulus silence.

    The function reads all audio files for the given trial using the `speaker_utils.read_all()` function, and then
    applies root-mean-square (RMS) normalization to each sound using the `speaker_utils.set_dba_level()` function. The
    resulting sounds are then padded to the length of the longest sound using the `speaker_utils.pad_to_longest()`
    function. Finally, the function returns a tuple containing the trial sounds and stimulus silence (an array of
    zeros with the same shape as the first sound in the trial sounds array).
    """
    # breakpoint()
    _, trial_sound = speaker_utils.read_all(trial[1])
    # unbox trial sound from list 
    trial_sound = speaker_utils.set_dba_level(trial_sound[0], DB_SPL)
 
    # sound = [speaker_utils.hann_window_front(signal, win_size=0.010, sr=44100) for signal in trial_sounds]
    return trial_sound


async def run_trial(
    trial: tuple,
    speaker_config: dict,
    ISI: float,
) -> None:
    """
    Run a single trial of the speech localization experiment
    """
    await route_trial_speakers(trial, speaker_config)
    sound = load_sounds(trial)
    sd.play(sound, 44100, blocking=False)


async def repeat_skipped_trials(
    *,
    repeat_trials: list,
    speaker_config: dict,
    block_start_sound: np.ndarray,
    block_start_soundsr: int,
    trial_count: int,
    responses: list,
) -> tuple[int, list]:
    """
    Repeats missed trials for the given list of trials and records participant's responses.

    Args:
    - repeat_trials: A list of `SemanticCueTrial` objects for which missed trials need to be repeated.
    - speaker_config: A dictionary containing information about the speakers.
    - block_start_sound: An array representing the sound played at the beginning of each block of trials.
    - block_start_soundsr: An integer representing the sampling rate of the `block_start_sound`.
    - reps_per_stim: An integer representing the number of times a stimulus is repeated.
    - exp_config: An object of type `SemanticCueConfig` containing experiment configuration details.
    - trial_count: An integer representing the current trial number.
    - responses: A list of `SemanticCueTrial` objects representing the responses given by the participant.
    - run_trial: A coroutine function that runs a trial.

    Returns:
    A tuple containing:
    - An integer representing the new trial count.
    - A list of `SemanticCueTrial` objects representing the participant's responses.
    """
    new_responses = responses[:]
    new_trial_count = trial_count
    input(
        f"Tell participant to get ready for the next block. Redoing skipped trials. Press enter when ready to start."
    )
    if len(repeat_trials) > 0:
        await speaker_utils.unroute_speaker((0, 0), speaker_config)
        await speaker_utils.route_speaker_on((0, 0), 0, speaker_config)
        sd.play(block_start_sound, block_start_soundsr, blocking=True)
        await speaker_utils.unroute_speaker((0, 0), speaker_config)

        input("Press enter when ready to continue")

    for trial in repeat_trials:
        response = ""
        await run_trial(trial, speaker_config, 0.5)
        response += input(f"({new_trial_count}) Subject Response: {response}")
        print(f"trial: {new_trial_count} {response=}")
        sd.wait()
        await speaker_utils.force_unroute_all(speaker_config)

        res = res = Trial(trial_count, trial[0:2], response)
        res.pres_num = new_trial_count
        # trial_order.append(new_trial_count)
        new_responses.append(res)
        new_trial_count += 1

    return new_trial_count, new_responses


async def run_experiment(
    speaker_config: dict,
    debug: bool = False,
    make_output_file: bool = True,
) -> list:
    """
    Run a semantic cueing experiment with the given trials and experimental configuration.

    Args:
    trials (list[tu.SemanticCueTrial]): The list of trials to run the experiment on.
    exp_config (cfg.SemanticCueConfig): The experimental configuration.
    speaker_config (dict): The configuration for the speakers.
    debug (bool): Whether to run the experiment in debug mode. Defaults to False.
    make_output_file (bool): Whether to save the trial results to a file. Defaults to True.
    reps_per_stim (int): The number of times each stimulus should be repeated. Defaults to 1.

    Returns:
    list[tu.SemanticCueTrial]: The list of trial results.
    """
    print(f"Running trial dict {EXPMT_TRIAL_DICT_PATH}")
    with open(EXPMT_TRIAL_DICT_PATH, 'rb') as f:
        trial_dict = pickle.load(f)

    if debug:
        speaker_utils.set_DAC(
            min_num_channels=2, device_keywords=["MacBook Pro Speakers"]
        )
    else:
        speaker_utils.set_DAC()

    ## Exp Setup
    responses: list[str] = []
    repeat_trials: list = []
    trial_count = 1
    break_soundsr, break_sound = wavfile.read('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/SpeakerArray/assets/sounds/three_tone.wav')
    block_start_soundsr, block_start_sound = wavfile.read('/Users/mcdermottspeakerarray/Documents/binaural_cocktail_party/SpeakerArray/assets/sounds/beep-01a.wav')
    break_sound = speaker_utils.set_dba_level(break_sound, DB_SPL)
    block_start_sound = speaker_utils.set_dba_level(block_start_sound, DB_SPL)

    input("press enter to start")

    for idx, trial in trial_dict.items(): # is 450 normally for this pilot 
        # import pdb; pdb.set_trace()
        ## Trial Setup
        await setup_trial(
            idx=idx,
            speaker_config=speaker_config,
            break_sound=break_sound,
            break_soundsr=break_soundsr,
            block_start_sound=block_start_sound,
            block_start_soundsr=block_start_soundsr,
            block_length=BLOCK_LEN,
            make_output_file=make_output_file,
            responses=responses
            )

        response = ""
        await run_trial(trial, speaker_config, 0.5)
        response += input(f"({trial_count}) Subject Response: {response}")
        print(f"trial: {trial_count} {response=}")
        print("-------------")
        sd.wait()
        await speaker_utils.force_unroute_all(speaker_config)

        ## Post Trial
        if "x" in response:
            repeat_trials.append(trial)
        else:
            res = Trial(trial_count, trial[:1], response)
            responses.append(res)
            if make_output_file:
                save_trials(responses, OUTPUT_FILE_NAME)
            trial_count += 1

    trial_count, responses = await repeat_skipped_trials(
        repeat_trials=repeat_trials,
        speaker_config=speaker_config,
        block_start_sound=block_start_sound,
        block_start_soundsr=block_start_soundsr,
        trial_count=trial_count,
        responses=responses,
    )
    ## Post Exp

    await speaker_utils.force_unroute_all(speaker_config)

    if make_output_file:
        save_trials(responses, OUTPUT_FILE_NAME)

    return responses


if __name__ == "__main__":
    asyncio.run(run_experiment(SPEAKER_CONFIG))
