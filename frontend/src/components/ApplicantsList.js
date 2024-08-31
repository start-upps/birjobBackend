import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

const ApplicantsList = ({ token }) => {
    const { jobId } = useParams();
    const [applicants, setApplicants] = useState([]);
    const [error, setError] = useState(null);

    useEffect(() => {
        axios.get(`http://127.0.0.1:8000/api/jobs/${jobId}/applicants/`, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
        .then(response => {
            setApplicants(response.data);
        })
        .catch(error => {
            console.error('Error fetching applicants:', error);
            setError('Failed to fetch applicants.');
        });
    }, [jobId, token]);

    if (error) {
        return <div>{error}</div>;
    }

    return (
        <div>
            <h1>Applicants</h1>
            {applicants.length > 0 ? (
                <ul>
                    {applicants.map(applicant => (
                        <li key={applicant.id}>
                            <p><strong>Name:</strong> {applicant.full_name}</p>
                            <p><strong>Email:</strong> {applicant.email}</p>
                            <p><strong>Phone:</strong> {applicant.phone}</p>
                            <p><strong>Cover Letter:</strong> {applicant.cover_letter}</p>
                            {/* Add more fields as necessary */}
                        </li>
                    ))}
                </ul>
            ) : (
                <p>No applicants yet.</p>
            )}
        </div>
    );
};

export default ApplicantsList;
