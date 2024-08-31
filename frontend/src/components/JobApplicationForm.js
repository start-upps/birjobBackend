import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { applyToJob } from '../api/api';

const JobApplicationForm = () => {
    const { id } = useParams();
    const [formData, setFormData] = useState({
        full_name: '',
        email: '',
        phone: '',
        cover_letter: '',
        resume: null,
    });
    const [error, setError] = useState(null);
    const navigate = useNavigate();

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

        applyToJob(id, data)
            .then(() => {
                alert('Application submitted successfully!');
                navigate('/');
            })
            .catch(error => {
                setError('Failed to submit application.');
            });
    };

    return (
        <div>
            <h1>Apply for Job</h1>
            {error && <p>{error}</p>}
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
};

export default JobApplicationForm;
