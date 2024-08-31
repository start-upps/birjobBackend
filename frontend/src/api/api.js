import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000/api';

// Fetch all jobs
export const fetchJobs = async () => {
    return await axios.get(`${API_URL}/jobs/jobs/`);
};

// Fetch a single job detail
export const fetchJobDetail = async (id, token) => {
    return await axios.get(`${API_URL}/jobs/${id}/`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
};

// Apply to a job
export const applyToJob = async (jobId, formData) => {  // No token required
    return await axios.post(`${API_URL}/jobs/${jobId}/apply/`, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
};


// Login a user
export const loginUser = async (credentials) => {
    return await axios.post(`${API_URL}/auth/login/`, credentials);
};

// Register a new user
export const registerUser = async (userData) => {
    return await axios.post(`${API_URL}/auth/register/`, userData);
};

// Post a job (for recruiters only)
export const postJob = async (jobData, token) => {
    return await axios.post(`${API_URL}/jobs/jobs/`, jobData, {
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
    });
};

// Update a job (for recruiters only)
export const updateJob = async (jobId, jobData, token) => {
    return await axios.put(`${API_URL}/jobs/${jobId}/`, jobData, {
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
    });
};

// Delete a job (for recruiters only)
export const deleteJob = async (jobId, token) => {
    return await axios.delete(`${API_URL}/jobs/jobs/${jobId}/`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
};
