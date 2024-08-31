import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { postJob } from '../api/api';

const PostJob = ({ token }) => {
    const [job, setJob] = useState({
        title: '',
        description: '',
        company: '',
        location: '',
        requirements: '',
    });
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    const handleChange = (e) => {
        setJob({
            ...job,
            [e.target.name]: e.target.value,
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        if (!token) {
            setError('You must be logged in to post a job.');
            return;
        }

        postJob(job, token)
            .then(() => {
                navigate('/jobs');  // Redirect to job listings after posting
            })
            .catch(() => {
                setError('Failed to post the job. Please try again.');
            });
    };

    return (
        <div>
            <h1>Post a Job</h1>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>Title</label>
                    <input type="text" name="title" value={job.title} onChange={handleChange} required />
                </div>
                <div>
                    <label>Description</label>
                    <textarea name="description" value={job.description} onChange={handleChange} required />
                </div>
                <div>
                    <label>Company</label>
                    <input type="text" name="company" value={job.company} onChange={handleChange} required />
                </div>
                <div>
                    <label>Location</label>
                    <input type="text" name="location" value={job.location} onChange={handleChange} required />
                </div>
                <div>
                    <label>Requirements</label>
                    <textarea name="requirements" value={job.requirements} onChange={handleChange} required />
                </div>
                {error && <p>{error}</p>}
                <button type="submit">Post Job</button>
            </form>
        </div>
    );
};

export default PostJob;
