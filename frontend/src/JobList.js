import React, { useEffect, useState } from 'react';
import axios from 'axios';

const JobList = () => {
    const [jobs, setJobs] = useState([]);

    useEffect(() => {
        axios.get('http://127.0.0.1:8000/api/jobs/')
            .then(response => {
                setJobs(response.data);
            })
            .catch(error => {
                console.error('There was an error fetching the jobs!', error);
            });
    }, []);

    return (
        <div>
            <h1>Job Listings</h1>
            <ul>
                {jobs.map(job => (
                    <li key={job.id}>{job.title} - {job.company}</li>
                ))}
            </ul>
        </div>
    );
};

export default JobList;
