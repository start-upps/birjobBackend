import React, { useEffect, useState } from 'react';
import api from './api'; // Import the Axios instance

function JobList() {
    const [jobs, setJobs] = useState([]);

    useEffect(() => {
        api.get('job-posts/')
            .then(response => {
                setJobs(response.data);
            })
            .catch(error => {
                console.error('Error fetching job posts:', error);
            });
    }, []);

    return (
        <div>
            <h1>Job Listings</h1>
            <ul>
                {jobs.map(job => (
                    <li key={job.id}>
                        <h2>{job.title}</h2>
                        <p>{job.description}</p>
                        <a href={`/jobs/${job.id}`}>View Details</a>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default JobList;
