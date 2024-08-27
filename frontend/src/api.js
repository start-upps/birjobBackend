import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000/api';

export const fetchJobs = (token) => {
    return axios.get(`${API_URL}/jobs/`, {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });
};

// Fetch details of a single job post
export const fetchJobDetail = (id, token) => {
    return axios.get(`${API_URL}/jobs/${id}/`, {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });
};

// Function to submit a job application
export const submitJobApplication = (data, token) => {
    return axios.post(`${API_URL}/job-applications/`, data, {
        headers: {
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${token}`,
        },
    });
};