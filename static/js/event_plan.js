   // Add new featuers
   function AddNewRule(event) {
    const timestamp = new Date().getTime(); 
    const newRuleHTML = `
    <div class="d-flex align-items-start mb-2 rule-container" id="rule_new_${timestamp}">
        <textarea class="form-control me-2" name="features" placeholder="Describe here ..." rows="2" required></textarea>
        <button type="button" class="btn btn-danger btn-sm" onclick="DeleteRule('${timestamp}')">
            <i class="fa-solid fa-trash"></i>
        </button>
    </div>
    `; 
    const rule_div = document.getElementById(event);
    if(rule_div){
        // rule_div.innerHTML += newRuleHTML;
        rule_div.insertAdjacentHTML("beforeend", newRuleHTML);
    }
    else {
        console.log("div not found: " + event);
    }
}


function DeleteRule(rule_id) {
    let ruleElement = document.getElementById('rule_' + rule_id);
    if(!ruleElement) {
        ruleElement = document.getElementById('rule_new_' + rule_id);
    }
    
    if (ruleElement) {
        if (confirm('Are you sure you want to delete this detail?')) {
            ruleElement.style.transition = 'opacity 0.3s';
            ruleElement.style.opacity = '0';
            
            setTimeout(() => {
                ruleElement.remove();
                updateRuleCount();
            }, 300);
        }
    } else {
        console.warn('Rule element not found:', rule_id);
    }
}


function updateRuleCount() {
    const ruleCount = document.querySelectorAll('.rule-container').length;
    console.log('Remaining rules:', ruleCount);
    
    const countElement = document.getElementById('ruleCount');
    if (countElement) {
        countElement.textContent = ruleCount;
    }
}
