import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { submitJobApplication } from './api';

function JobApplicationForm() {
    const { id } = useParams();
    const [formData, setFormData] = useState({
        full_name: '',
        email: '',
        phone: '',
        cover_letter: '',
        resume: null,
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value,
        });
    };

    const handleFileChange = (e) => {
        setFormData({
            ...formData,
            resume: e.target.files[0],
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        const data = new FormData();
        data.append('job', id);
        data.append('full_name', formData.full_name);
        data.append('email', formData.email);
        data.append('phone', formData.phone);
        data.append('cover_letter', formData.cover_letter);
        data.append('resume', formData.resume);

        const token = localStorage.getItem('accessToken');
        if (token) {
            submitJobApplication(data, token)
                .then(response => {
                    alert('Application submitted successfully!');
                })
                .catch(error => {
                    console.error('Error submitting application:', error);
                });
        } else {
            console.error('No access token found');
        }
    };

    return (
        <div>
            <h1>Apply for Job</h1>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>Full Name</label>
                    <input type="text" name="full_name" value={formData.full_name} onChange={handleChange} required />
                </div>
                <div>
                    <label>Email</label>
                    <input type="email" name="email" value={formData.email} onChange={handleChange} required />
                </div>
                <div>
                    <label>Phone</label>
                    <input type="text" name="phone" value={formData.phone} onChange={handleChange} required />
                </div>
                <div>
                    <label>Cover Letter</label>
                    <textarea name="cover_letter" value={formData.cover_letter} onChange={handleChange}></textarea>
                </div>
                <div>
                    <label>Resume</label>
                    <input type="file" name="resume" onChange={handleFileChange} required />
                </div>
                <button type="submit">Submit Application</button>
            </form>
        </div>
    );
}

export default JobApplicationForm;
