import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000/api';

export const fetchJobs = async (token) => {
    return await axios.get(`${API_URL}/jobs/`, {
    });
};

export const fetchJobDetail = async (id, token) => {
    return await axios.get(`${API_URL}/jobs/${id}/`, {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });
};

export const applyToJob = async (jobId, formData, token) => {
    return await axios.post(`${API_URL}/jobs/${jobId}/apply/`, formData, {
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
        }
    });
};

export const loginUser = async (credentials) => {
    return await axios.post(`${API_URL}/auth/login/`, credentials);
};

export const registerUser = async (userData) => {
    return await axios.post(`${API_URL}/auth/register/`, userData);
};
