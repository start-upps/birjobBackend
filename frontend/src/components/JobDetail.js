import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { fetchJobDetail } from '../api/api';

const JobDetail = () => {
    const { id } = useParams();
    const [job, setJob] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        
        if (token) {
            fetchJobDetail(id, token)
                .then(response => {
                    setJob(response.data);
                })
                .catch(error => {
                    console.error('Error fetching job details:', error);
                    setError('Failed to fetch job details.');
                });
        } else {
            setError('You must be logged in to view job details.');
        }
    }, [id]);

    if (error) return <div>{error}</div>;

    if (!job) return <div>Loading...</div>;

    return (
        <div>
            <h1>{job.title}</h1>
            <p>{job.description}</p>
            <p>Company: {job.company}</p>
            <p>Location: {job.location}</p>
            <a href={`/apply/${job.id}`}>Apply Now</a>
        </div>
    );
};

export default JobDetail;
