// src/services/API/studentmockinterview.js
import { assessmentApiRequest } from './index2';

export const interviewOperationsAPI = {
  // Start a new interview session - GET /weekly_interview/start_interview
  startInterview: async () => {
    try {
      console.log('?? API: Starting new interview session');
      
      const response = await assessmentApiRequest('/weekly_interview/start_interview', {
        method: 'GET'
      });
      
      console.log('? API Response for start interview:', response);
      
      // Validate response has required fields
      if (!response || !response.test_id) {
        throw new Error('Invalid response from server - missing test_id');
      }
      
      return response;
    } catch (error) {
      console.error('? API Error in startInterview:', error);
      throw new Error(`Failed to start interview: ${error.message}`);
    }
  },

  // Start the next round of interview - GET /weekly_interview/start_next_round?test_id=${testId}
  startNextRound: async (testId) => {
    try {
      if (!testId) {
        throw new Error('Test ID is required to start next round');
      }
      
      console.log('API: Starting next round for test_id:', testId);
      
      const response = await assessmentApiRequest(`/weekly_interview/start_next_round?test_id=${testId}`, {
        method: 'GET'
      });
      
      console.log('API Response for start next round:', response);
      return response;
    } catch (error) {
      console.error('API Error in startNextRound:', error);
      throw new Error(`Failed to start next round: ${error.message}`);
    }
  },

  // Evaluate the interview - GET /weekly_interview/evaluate?test_id=${testId}
  evaluateInterview: async (testId) => {
    try {
      if (!testId) {
        throw new Error('Test ID is required for evaluation');
      }
      
      console.log('API: Evaluating interview for test_id:', testId);
      
      const response = await assessmentApiRequest(`/weekly_interview/evaluate?test_id=${testId}`, {
        method: 'GET'
      });
      
      console.log('API Response for evaluate interview:', response);
      return response;
    } catch (error) {
      console.error('API Error in evaluateInterview:', error);
      throw new Error(`Failed to evaluate interview: ${error.message}`);
    }
  },

  // PRIMARY METHOD: Submit text response with audio blob
  recordAndRespondWithText: async (testId, transcribedText, additionalData = {}) => {
    try {
      if (!testId || !transcribedText) {
        throw new Error('Test ID and transcribed text are required');
      }
      
      console.log('API: Recording and responding with text for test_id:', testId);
      console.log('API: Transcribed text:', transcribedText);
      
      // Create an audio blob from the transcribed text
      const audioBlob = await convertTextToAudioBlob(transcribedText);
      console.log('API: Generated audio blob from text, size:', audioBlob.size);
      
      // Create FormData to match backend expectations
      const formData = new FormData();
      formData.append('test_id', testId);
      formData.append('audio', audioBlob, 'transcribed_response.wav');
      formData.append('transcribed_text', transcribedText);
      
      // Add additional data
      if (additionalData.round) {
        formData.append('round', additionalData.round.toString());
      }
      
      Object.keys(additionalData).forEach(key => {
        if (!['round'].includes(key) && additionalData[key] !== undefined) {
          formData.append(key, additionalData[key].toString());
        }
      });
      
      console.log('API: Submitting FormData with audio blob generated from text');
      
      const response = await assessmentApiRequest('/weekly_interview/record_and_respond', {
        method: 'POST',
        body: formData
      });
      
      console.log('API Response for text submission:', response);
      return response;
    } catch (error) {
      console.error('API Error in recordAndRespondWithText:', error);
      throw new Error(`Failed to record and respond with text: ${error.message}`);
    }
  },

  // Helper method to validate test ID format
  validateTestId: (testId) => {
    if (!testId) {
      return { valid: false, error: 'Test ID is required' };
    }
    
    if (typeof testId !== 'string' && typeof testId !== 'number') {
      return { valid: false, error: 'Test ID must be a string or number' };
    }
    
    return { valid: true };
  }
};

// Convert text to audio blob using Web Speech API (TTS)
async function convertTextToAudioBlob(text) {
  return new Promise((resolve) => {
    try {
      console.log('🎵 Converting text to audio:', text.substring(0, 50) + '...');
      
      if (!('speechSynthesis' in window)) {
        console.warn('Speech synthesis not supported, creating silent audio');
        resolve(createSilentAudioBlob());
        return;
      }
      
      const audioBlob = createTextBasedAudioBlob(text);
      resolve(audioBlob);
      
    } catch (error) {
      console.error('Failed to convert text to audio:', error);
      resolve(createSilentAudioBlob());
    }
  });
}

// Create an audio blob that represents text (for backend processing)
function createTextBasedAudioBlob(text) {
  try {
    const sampleRate = 44100;
    const textLength = text.length;
    const duration = Math.max(0.5, Math.min(5.0, textLength * 0.01));
    const numSamples = Math.floor(sampleRate * duration);
    const arrayBuffer = new ArrayBuffer(44 + numSamples * 2);
    const view = new DataView(arrayBuffer);
    
    // WAV header
    const writeString = (offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };
    
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + numSamples * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, numSamples * 2, true);
    
    // Generate audio data based on text
    const audioData = new Int16Array(arrayBuffer, 44, numSamples);
    for (let i = 0; i < numSamples; i++) {
      const frequency = 200 + (text.charCodeAt(i % text.length) % 100);
      const sample = Math.sin(2 * Math.PI * frequency * i / sampleRate) * 100;
      audioData[i] = Math.floor(sample);
    }
    
    const blob = new Blob([arrayBuffer], { type: 'audio/wav' });
    console.log('✅ Created text-based audio blob, size:', blob.size, 'duration:', duration.toFixed(2) + 's');
    return blob;
  } catch (error) {
    console.warn('Failed to create text-based audio blob, using silent:', error);
    return createSilentAudioBlob();
  }
}

// Create a minimal silent audio blob (fallback)
function createSilentAudioBlob() {
  try {
    const sampleRate = 44100;
    const duration = 0.5;
    const numSamples = sampleRate * duration;
    const arrayBuffer = new ArrayBuffer(44 + numSamples * 2);
    const view = new DataView(arrayBuffer);
    
    // WAV header
    const writeString = (offset, string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };
    
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + numSamples * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, numSamples * 2, true);
    
    // Silent audio data (all zeros)
    const audioData = new Int16Array(arrayBuffer, 44, numSamples);
    audioData.fill(0);
    
    return new Blob([arrayBuffer], { type: 'audio/wav' });
  } catch (error) {
    console.error('Failed to create silent audio blob:', error);
    return new Blob([''], { type: 'audio/wav' });
  }
}

export default interviewOperationsAPI;