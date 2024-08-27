import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import JobList from './JobList';
// Import other components as needed

function App() {
    return (
        <Router>
            <Switch>
                <Route exact path="/" component={JobList} />
                {/* Define other routes as needed */}
            </Switch>
        </Router>
    );
}

export default App;
