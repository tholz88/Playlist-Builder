import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstance()
def hudsonRealm = new HudsonPrivateSecurityRealm(false)

def adminUser = System.getenv("JENKINS_ADMIN_ID") ?: "admin"
def adminPass = System.getenv("JENKINS_ADMIN_PASSWORD") ?: "admin"

if (!hudsonRealm.getUser(adminUser)) {
    hudsonRealm.createAccount(adminUser, adminPass)
}
instance.setSecurityRealm(hudsonRealm)
def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)
instance.save()