import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { fetchJobDetail } from '../api/api';

const JobDetail = () => {
    const { id } = useParams();
    const [job, setJob] = useState(null);

    useEffect(() => {
        const token = localStorage.getItem('accessToken');
        fetchJobDetail(id, token)
            .then(response => {
                setJob(response.data);
            })
            .catch(error => {
                console.error('Error fetching job details:', error);
            });
    }, [id]);

    if (!job) return <div>Loading...</div>;

    return (
        <div>
            <h1>{job.title}</h1>
            <p>{job.description}</p>
            <p>{job.company}</p>
            <p>{job.location}</p>
            <a href={`/apply/${job.id}`}>Apply Now</a>
        </div>
    );
};

export default JobDetail;
