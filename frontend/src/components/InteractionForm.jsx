import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { updateFormField, saveInteraction } from '../store/crmSlice';

const sentimentOptions = ['Positive', 'Neutral', 'Negative'];
const interactionTypes = ['Meeting', 'Call', 'Conference', 'Email', 'Other'];

const InteractionForm = () => {
  const dispatch = useDispatch();
  const formData = useSelector((state) => state.crm.formData);
  const loading = useSelector((state) => state.crm.loading);

  const handleChange = (e) => {
    const { name, value } = e.target;
    dispatch(updateFormField({ field: name, value }));
  };

  const handleSave = () => {
    dispatch(saveInteraction(formData));
  };

  return (
    <div className="interaction-form">
      <h2>Log HCP Interaction</h2>
      <form>
        <div className="form-group">
          <label>HCP Name</label>
          <input
            type="text"
            name="hcp_name"
            value={formData.hcp_name}
            onChange={handleChange}
            placeholder="Dr. Smith"
          />
        </div>

        <div className="form-group">
          <label>Interaction Type</label>
          <select
            name="interaction_type"
            value={formData.interaction_type}
            onChange={handleChange}
          >
            {interactionTypes.map((type) => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Date</label>
            <input
              type="date"
              name="date"
              value={formData.date}
              onChange={handleChange}
            />
          </div>
          <div className="form-group">
            <label>Time</label>
            <input
              type="time"
              name="time"
              value={formData.time}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="form-group">
          <label>Attendees</label>
          <input
            type="text"
            name="attendees"
            value={formData.attendees}
            onChange={handleChange}
            placeholder="Other attendees"
          />
        </div>

        <div className="form-group">
          <label>Topics Discussed</label>
          <textarea
            name="topics_discussed"
            value={formData.topics_discussed}
            onChange={handleChange}
            placeholder="Product efficacy, clinical data..."
            rows="2"
          />
        </div>

        <div className="form-group">
          <label>Voice Note Summary</label>
          <textarea
            name="voice_note_summary"
            value={formData.voice_note_summary}
            onChange={handleChange}
            placeholder="Summary of the conversation..."
            rows="2"
          />
        </div>

        <div className="form-group">
          <label>Materials Shared</label>
          <input
            type="text"
            name="materials_shared"
            value={formData.materials_shared}
            onChange={handleChange}
            placeholder="Brochure, clinical data, samples..."
          />
        </div>

        <div className="form-group">
          <label>Samples Distributed</label>
          <input
            type="text"
            name="samples_distributed"
            value={formData.samples_distributed}
            onChange={handleChange}
            placeholder="Product samples given..."
          />
        </div>

        <div className="form-group">
          <label>HCP Sentiment</label>
          <select
            name="hcp_sentiment"
            value={formData.hcp_sentiment}
            onChange={handleChange}
          >
            {sentimentOptions.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Outcomes</label>
          <textarea
            name="outcomes"
            value={formData.outcomes}
            onChange={handleChange}
            placeholder="Key outcomes from the meeting..."
            rows="2"
          />
        </div>

        <div className="form-group">
          <label>Follow-up Actions</label>
          <textarea
            name="follow_up_actions"
            value={formData.follow_up_actions}
            onChange={handleChange}
            placeholder="Schedule follow-up meeting, send additional data..."
            rows="2"
          />
        </div>

        <div className="form-actions">
          <button
            type="button"
            className="save-button"
            onClick={handleSave}
            disabled={loading}
          >
            {loading ? 'Saving...' : 'Save Interaction'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default InteractionForm;
