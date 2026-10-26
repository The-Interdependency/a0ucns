export const PATTERN_OPTIONS = [
  { value: 'fan_out', label: 'Fan Out', description: 'Parallel call to many isolated instances' },
  { value: 'daisy_chain', label: 'Daisy Chain', description: 'Sequential instance-to-instance chaining' },
  { value: 'room_all', label: 'Room All', description: 'Everyone sees everyone each round' },
  { value: 'room_synthesized', label: 'Room Synthesized', description: 'One synthesizer drives the next round' },
  { value: 'council', label: 'Council', description: 'Each instance synthesizes the whole room' },
  { value: 'roleplay', label: 'Roleplay', description: 'DM + players with initiative and reactions' },
];

export const INPUT_MODE_OPTIONS = [
  { value: 'root_plus_previous', label: 'Root + previous outputs' },
  { value: 'root_prompt', label: 'Root prompt only' },
  { value: 'previous_outputs', label: 'Previous outputs only' },
];

export const ROLE_PRESET_OPTIONS = [
  "devil's advocate",
  'optimist',
  'pessimist',
  'moderator',
  'contrarian',
  'leader',
  'follower',
  'introvert',
  'extrovert',
  'mediator',
  'warrior',
  'mage',
  'rogue',
  'healer',
  'scholar',
  'trickster',
  'bard',
];

export function createEmptyStage() {
  return {
    name: '',
    pattern: 'fan_out',
    prompt: '',
    input_mode: 'root_plus_previous',
    participants: [],
    rounds: '',
    max_history: '',
    verbosity: '',
    include_original_prompt: true,
    synthesis_prompt: 'Synthesize and analyze these AI responses:',
    synthesis_instance_id: '',
    synthesis_group_id: '',
    player_participants: [],
    dm_instance_id: '',
    dm_group_id: '',
    action_word_limit: '',
    use_initiative: true,
    allow_reactions: false,
  };
}
