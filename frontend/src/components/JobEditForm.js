import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchJobDetail, updateJob, deleteJob } from '../api/api';

const JobEditForm = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [job, setJob] = useState({
        title: '',
        description: '',
        company: '',
        location: '',
        requirements: '',
    });
    const [error, setError] = useState(null);

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        fetchJobDetail(id, token)
            .then(response => {
                setJob(response.data);
            })
            .catch(error => {
                setError('Failed to load job details.');
            });
    }, [id]);

    const handleChange = (e) => {
        setJob({
            ...job,
            [e.target.name]: e.target.value,
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        const token = localStorage.getItem('access_token');
        updateJob(id, job, token)
            .then(() => {
                navigate('/jobs/');
            })
            .catch(error => {
                setError('Failed to update the job.');
            });
    };

    const handleDelete = () => {
        const token = localStorage.getItem('access_token');
        deleteJob(id, token)
            .then(() => {
                navigate('/jobs/');
            })
            .catch(error => {
                setError('Failed to delete the job.');
            });
    };

    return (
        <div>
            <h1>Edit Job</h1>
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
                <button type="submit">Update Job</button>
                <button type="button" onClick={handleDelete}>Delete Job</button>
            </form>
        </div>
    );
};

export default JobEditForm;
