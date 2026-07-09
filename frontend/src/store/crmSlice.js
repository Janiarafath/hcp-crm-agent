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
};

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
      const data = action.payload;
      if (data.hcp_name) state.formData.hcp_name = data.hcp_name;
      if (data.interaction_type) state.formData.interaction_type = data.interaction_type;
      if (data.date) state.formData.date = data.date;
      if (data.time) state.formData.time = data.time;
      if (data.attendees) state.formData.attendees = data.attendees;
      if (data.topics_discussed) state.formData.topics_discussed = data.topics_discussed;
      if (data.voice_note_summary) state.formData.voice_note_summary = data.voice_note_summary;
      if (data.materials_shared) state.formData.materials_shared = data.materials_shared;
      if (data.samples_distributed) state.formData.samples_distributed = data.samples_distributed;
      if (data.hcp_sentiment) state.formData.hcp_sentiment = data.hcp_sentiment;
      if (data.outcomes) state.formData.outcomes = data.outcomes;
      if (data.follow_up_actions) state.formData.follow_up_actions = data.follow_up_actions;
    },
    clearError: (state) => {
      state.error = null;
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
            
            if (call.tool === 'log_interaction' && args.interaction_data) {
              const data = typeof args.interaction_data === 'string' 
                ? JSON.parse(args.interaction_data) 
                : args.interaction_data;
              state.formData = { ...state.formData, ...data };
            }
            
            if (call.tool === 'edit_interaction' && args.field_name && args.field_value) {
              state.formData[args.field_name] = args.field_value;
            }
            
            if (call.tool === 'get_interaction_history') {
              const result = typeof call.result === 'string' ? JSON.parse(call.result) : call.result;
              if (result.data) {
                const { hcp_name, interaction_type, date, time, attendees, topics_discussed, voice_note_summary, materials_shared, samples_distributed, hcp_sentiment, outcomes, follow_up_actions } = result.data;
                state.formData = {
                  hcp_name: hcp_name || '',
                  interaction_type: interaction_type || 'Meeting',
                  date: date || '',
                  time: time || '',
                  attendees: attendees || '',
                  topics_discussed: topics_discussed || '',
                  voice_note_summary: voice_note_summary || '',
                  materials_shared: materials_shared || '',
                  samples_distributed: samples_distributed || '',
                  hcp_sentiment: hcp_sentiment || 'Neutral',
                  outcomes: outcomes || '',
                  follow_up_actions: follow_up_actions || '',
                };
              }
            }
          }
        }
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
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
      })
      .addCase(saveInteraction.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { updateFormField, resetForm, addChatMessage, populateForm, clearError } = crmSlice.actions;
export default crmSlice.reducer;
