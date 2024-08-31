import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchJobDetail, updateJob } from '../api/api';

const EditJob = ({ token }) => {
    const { id } = useParams();
    const [job, setJob] = useState({
        title: '',
        description: '',
        company: '',
        location: '',
        requirements: '',
    });
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        if (token) {
            fetchJobDetail(id, token)
                .then(response => {
                    setJob(response.data);
                })
                .catch(error => {
                    setError('Failed to fetch job details');
                });
        } else {
            setError('You must be logged in to edit a job');
        }
    }, [id, token]);

    const handleChange = (e) => {
        setJob({
            ...job,
            [e.target.name]: e.target.value,
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        updateJob(id, job, token)
            .then(() => {
                navigate('/jobs');
            })
            .catch(error => {
                setError('Failed to update the job. Please try again.');
            });
    };

    return (
        <div>
            <h1>Edit Job</h1>
            {error && <p>{error}</p>}
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
                <button type="submit">Update Job</button>
            </form>
        </div>
    );
};

export default EditJob;
