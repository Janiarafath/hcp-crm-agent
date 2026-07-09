import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { chatWithAgent, getInteractions, createInteraction } from '../services/api';

export const sendMessage = createAsyncThunk(
  'crm/sendMessage',
  async (message, { rejectWithValue }) => {
    try {
      const response = await chatWithAgent(message);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to send message');
    }
  }
);

export const fetchInteractions = createAsyncThunk(
  'crm/fetchInteractions',
  async (_, { rejectWithValue }) => {
    try {
      const response = await getInteractions();
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch interactions');
    }
  }
);

export const saveInteraction = createAsyncThunk(
  'crm/saveInteraction',
  async (interactionData, { rejectWithValue }) => {
    try {
      const response = await createInteraction(interactionData);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to save interaction');
    }
  }
);

const initialState = {
  formData: {
    hcp_name: '',
    interaction_type: 'Meeting',
    date: '',
    time: '',
    attendees: '',
    topics_discussed: '',
    voice_note_summary: '',
    materials_shared: '',
    samples_distributed: '',
    hcp_sentiment: 'Neutral',
    outcomes: '',
    follow_up_actions: '',
  },
  chatMessages: [],
  interactions: [],
  loading: false,
  error: null,
  lastInteractionId: null,
  toast: null,
};

const FIELD_MAP = {
  hcp_name: 'hcp_name',
  doctor_name: 'hcp_name',
  interaction_type: 'interaction_type',
  date: 'date',
  time: 'time',
  attendees: 'attendees',
  topic: 'topics_discussed',
  topics: 'topics_discussed',
  topics_discussed: 'topics_discussed',
  discussion_topics: 'topics_discussed',
  sentiment: 'hcp_sentiment',
  hcp_sentiment: 'hcp_sentiment',
  material: 'materials_shared',
  materials: 'materials_shared',
  materials_shared: 'materials_shared',
  shared_materials: 'materials_shared',
  samples: 'samples_distributed',
  samples_distributed: 'samples_distributed',
  outcomes: 'outcomes',
  outcome: 'outcomes',
  follow_up: 'follow_up_actions',
  follow_up_actions: 'follow_up_actions',
  followup: 'follow_up_actions',
  voice_note: 'voice_note_summary',
  voice_note_summary: 'voice_note_summary',
  summary: 'voice_note_summary',
  attendees: 'attendees',
  notes: 'voice_note_summary',
};

const SENTIMENT_MAP = {
  'positive': 'Positive',
  'neutral': 'Neutral',
  'negative': 'Negative',
};

function normalizeValue(field, value) {
  if (Array.isArray(value)) value = value.join(', ');
  if (typeof value === 'object' && value !== null) value = String(value);
  if (field === 'hcp_sentiment' && typeof value === 'string') {
    const lower = value.toLowerCase();
    return SENTIMENT_MAP[lower] || value;
  }
  return value;
}

function mapLLMDataToForm(data) {
  const mapped = {};
  for (const [key, value] of Object.entries(data)) {
    const formKey = FIELD_MAP[key];
    if (formKey && value !== null && value !== undefined && value !== '') {
      mapped[formKey] = normalizeValue(formKey, value);
    }
  }
  return mapped;
}

const crmSlice = createSlice({
  name: 'crm',
  initialState,
  reducers: {
    updateFormField: (state, action) => {
      const { field, value } = action.payload;
      state.formData[field] = value;
    },
    resetForm: (state) => {
      state.formData = initialState.formData;
    },
    addChatMessage: (state, action) => {
      state.chatMessages.push(action.payload);
    },
    populateForm: (state, action) => {
      const mapped = mapLLMDataToForm(action.payload);
      state.formData = { ...state.formData, ...mapped };
    },
    clearError: (state) => {
      state.error = null;
    },
    loadInteractionIntoForm: (state, action) => {
      const data = action.payload;
      state.formData = {
        hcp_name: data.hcp_name || '',
        interaction_type: data.interaction_type || 'Meeting',
        date: data.date || '',
        time: data.time || '',
        attendees: data.attendees || '',
        topics_discussed: data.topics_discussed || '',
        voice_note_summary: data.voice_note_summary || '',
        materials_shared: data.materials_shared || '',
        samples_distributed: data.samples_distributed || '',
        hcp_sentiment: data.hcp_sentiment || 'Neutral',
        outcomes: data.outcomes || '',
        follow_up_actions: data.follow_up_actions || '',
      };
    },
    clearToast: (state) => {
      state.toast = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.loading = false;
        const { response, tool_calls } = action.payload;

        state.chatMessages.push({
          role: 'assistant',
          content: response,
          toolCalls: tool_calls,
        });

        if (tool_calls) {
          for (const call of tool_calls) {
            const args = typeof call.args === 'string' ? JSON.parse(call.args) : call.args;

            if (call.tool === 'log_interaction') {
              if (args.interaction_data) {
                let data;
                try {
                  data = typeof args.interaction_data === 'string'
                    ? JSON.parse(args.interaction_data)
                    : args.interaction_data;
                } catch {
                  data = {};
                }
                const mapped = mapLLMDataToForm(data);
                state.formData = { ...state.formData, ...mapped };
              }
              const result = typeof call.result === 'string' ? JSON.parse(call.result) : call.result;
              if (result?.status === 'success') {
                state.lastInteractionId = result.interaction_id;
                state.toast = { type: 'success', message: `Interaction #${result.interaction_id} logged successfully` };
              }
            }

            if (call.tool === 'edit_interaction' && args.field_name && args.field_value) {
              const formKey = FIELD_MAP[args.field_name] || args.field_name;
              state.formData[formKey] = normalizeValue(formKey, args.field_value);
              const result = typeof call.result === 'string' ? JSON.parse(call.result) : call.result;
              if (result?.status === 'success') {
                state.toast = { type: 'success', message: `Updated: ${args.field_name} changed` };
              }
            }

            if (call.tool === 'create_follow_up') {
              const result = typeof call.result === 'string' ? JSON.parse(call.result) : call.result;
              if (result?.follow_up_actions) {
                state.formData.follow_up_actions = result.follow_up_actions;
              }
              if (result?.status === 'success') {
                state.toast = { type: 'success', message: 'Follow-up action added' };
              }
            }

            if (call.tool === 'get_interaction_history') {
              const result = typeof call.result === 'string' ? JSON.parse(call.result) : call.result;
              if (result?.data) {
                const d = result.data;
                state.formData = {
                  hcp_name: d.hcp_name || '',
                  interaction_type: d.interaction_type || 'Meeting',
                  date: d.date || '',
                  time: d.time || '',
                  attendees: d.attendees || '',
                  topics_discussed: d.topics_discussed || '',
                  voice_note_summary: d.voice_note_summary || '',
                  materials_shared: d.materials_shared || '',
                  samples_distributed: d.samples_distributed || '',
                  hcp_sentiment: d.hcp_sentiment || 'Neutral',
                  outcomes: d.outcomes || '',
                  follow_up_actions: d.follow_up_actions || '',
                };
              }
            }
          }
        }
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
        state.toast = { type: 'error', message: action.payload || 'Request failed' };
      })
      .addCase(fetchInteractions.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.loading = false;
        state.interactions = action.payload;
      })
      .addCase(fetchInteractions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(saveInteraction.pending, (state) => {
        state.loading = true;
      })
      .addCase(saveInteraction.fulfilled, (state, action) => {
        state.loading = false;
        state.lastInteractionId = action.payload.id;
        state.toast = { type: 'success', message: 'Interaction saved manually' };
      })
      .addCase(saveInteraction.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
        state.toast = { type: 'error', message: action.payload || 'Save failed' };
      });
  },
});

export const { updateFormField, resetForm, addChatMessage, populateForm, clearError, loadInteractionIntoForm, clearToast } = crmSlice.actions;
export default crmSlice.reducer;
