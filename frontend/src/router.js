import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import JobList from './components/JobList';
import JobDetail from './components/JobDetail';
import JobApplicationForm from './components/JobApplicationForm';
import Login from './components/Login';

function App() {
    return (
        <Router>
            <Switch>
                <Route exact path="/" component={JobList} />
                <Route path="/jobs/:id" component={JobDetail} />
                <Route path="/apply/:id" component={JobApplicationForm} />
                <Route path="/login" component={Login} />
            </Switch>
        </Router>
    );
}

export default App;
