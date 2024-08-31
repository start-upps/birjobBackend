import React, { useEffect, useState } from 'react';
import { fetchJobs, deleteJob } from '../api/api';
import { useNavigate } from 'react-router-dom';

const JobList = ({ token }) => {
    const [jobs, setJobs] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        fetchJobs()
            .then(response => {
                if (Array.isArray(response.data)) {
                    setJobs(response.data);
                } else {
                    setJobs([]);
                }
                setLoading(false);
            })
            .catch(error => {
                console.error('Error fetching jobs:', error);
                setError('Failed to fetch jobs.');
                setLoading(false);
            });
    }, []);

    const handleDelete = (jobId) => {
        if (window.confirm('Are you sure you want to delete this job?')) {
            deleteJob(jobId, token)
                .then(() => {
                    setJobs(jobs.filter(job => job.id !== jobId));
                })
                .catch(error => {
                    console.error('Error deleting job:', error);
                    setError('Failed to delete job.');
                });
        }
    };

    if (loading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div>{error}</div>;
    }

    return (
        <div>
            <h1>Job Listings</h1>
            {token && (
                <button onClick={() => navigate('/post-job')}>Post New Job</button>
            )}
            {jobs.length > 0 ? (
                <ul>
                    {jobs.map(job => (
                        <li key={job.id}>
                            <h2>{job.title}</h2>
                            <p><strong>Company:</strong> {job.company}</p>
                            <p><strong>Location:</strong> {job.location}</p>
                            <p><strong>Description:</strong> {job.description}</p>
                            <p><strong>Requirements:</strong> {job.requirements}</p>
                            <p><strong>Posted At:</strong> {new Date(job.posted_at).toLocaleString()}</p>
                            {token && (
                                <>
                                    <button onClick={() => navigate(`/edit-job/${job.id}`)}>Edit</button>
                                    <button onClick={() => handleDelete(job.id)}>Delete</button>
                                    <button onClick={() => navigate(`/jobs/${job.id}/applicants`)}>View Applicants</button> {/* New Button */}
                                </>
                            )}
                        </li>
                    ))}
                </ul>
            ) : (
                <p>No jobs available.</p>
            )}
        </div>
    );
};

export default JobList;
